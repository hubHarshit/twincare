from typing import Dict, Any, Optional
import json
from datetime import datetime
import redis
from redis.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import RedisError, ConnectionError
from ..config.redis_config import RedisConfig
from ..utils.encryption import EncryptionService, EncryptionError
import logging

logger = logging.getLogger(__name__)

class ContextManager:
    def __init__(self):
        # Configure Redis connection pool
        self.pool = redis.ConnectionPool(
            host=RedisConfig.HOST,
            port=RedisConfig.PORT,
            db=RedisConfig.DB,
            password=RedisConfig.PASSWORD,
            ssl=RedisConfig.SSL,
            decode_responses=True,
            max_connections=10
        )
        
        # Configure retry strategy
        retry = Retry(
            ExponentialBackoff(),
            retries=3,
            timeout=30
        )
        
        self.redis_client = redis.Redis(
            connection_pool=self.pool,
            retry=retry
        )
        
        self.encryption_service = EncryptionService()
        self.ttl = RedisConfig.TTL

    def _get_key(self, user_id: str) -> str:
        """Generate Redis key for user context"""
        return f"context:{user_id}"

    def _handle_redis_error(self, operation: str, error: Exception) -> None:
        """Handle Redis errors with logging"""
        logger.error(f"Redis {operation} failed: {str(error)}")
        raise RedisError(f"Redis {operation} failed: {str(error)}")

    def get_context(self, user_id: str) -> Dict[str, Any]:
        """Get context from Redis with decryption and error handling"""
        try:
            key = self._get_key(user_id)
            encrypted_data = self.redis_client.get(key)
            
            if not encrypted_data:
                # Initialize new context if none exists
                context = {
                    'created_at': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat(),
                    'interactions': [],
                    'agent_state': {}
                }
                self.update_context(user_id, context)
                return context

            # Decrypt and parse context
            decrypted_data = self.encryption_service.decrypt(encrypted_data)
            return json.loads(decrypted_data)
            
        except RedisError as e:
            self._handle_redis_error("get", e)
        except EncryptionError as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {str(e)}")
            raise ValueError(f"Invalid context data: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in get_context: {str(e)}")
            raise

    def update_context(self, user_id: str, new_context: Dict[str, Any]) -> None:
        """Update context in Redis with encryption and error handling"""
        try:
            key = self._get_key(user_id)
            current_context = self.get_context(user_id)
            
            # Update context
            current_context.update(new_context)
            current_context['last_updated'] = datetime.now().isoformat()
            
            # Encrypt and store
            encrypted_data = self.encryption_service.encrypt(json.dumps(current_context))
            self.redis_client.setex(key, self.ttl, encrypted_data)
            
        except RedisError as e:
            self._handle_redis_error("update", e)
        except EncryptionError as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in update_context: {str(e)}")
            raise

    def save_context(self, user_id: str, filepath: str) -> None:
        """Save context to file (for backup) with error handling"""
        try:
            context = self.get_context(user_id)
            with open(filepath, 'w') as f:
                json.dump(context, f)
        except Exception as e:
            logger.error(f"Failed to save context to file: {str(e)}")
            raise

    def load_context(self, user_id: str, filepath: str) -> None:
        """Load context from file and store in Redis with error handling"""
        try:
            with open(filepath, 'r') as f:
                context = json.load(f)
            self.update_context(user_id, context)
        except Exception as e:
            logger.error(f"Failed to load context from file: {str(e)}")
            raise

    def delete_context(self, user_id: str) -> None:
        """Delete context from Redis with error handling"""
        try:
            key = self._get_key(user_id)
            self.redis_client.delete(key)
        except RedisError as e:
            self._handle_redis_error("delete", e)
        except Exception as e:
            logger.error(f"Unexpected error in delete_context: {str(e)}")
            raise 