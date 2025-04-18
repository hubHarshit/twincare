from typing import Optional
import os
from dotenv import load_dotenv
import secrets

load_dotenv()

def validate_env_vars():
    """Validate required environment variables"""
    required_vars = {
        'REDIS_PASSWORD': os.getenv('REDIS_PASSWORD'),
        'ENCRYPTION_KEY': os.getenv('ENCRYPTION_KEY')
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

class RedisConfig:
    HOST: str = os.getenv('REDIS_HOST', 'localhost')
    PORT: int = int(os.getenv('REDIS_PORT', 6379))
    DB: int = int(os.getenv('REDIS_DB', 0))
    PASSWORD: Optional[str] = os.getenv('REDIS_PASSWORD')
    SSL: bool = os.getenv('REDIS_SSL', 'true').lower() == 'true'
    TTL: int = int(os.getenv('REDIS_TTL', 86400))  # 24 hours in seconds
    
    @classmethod
    def validate(cls):
        """Validate Redis configuration"""
        if not cls.PASSWORD:
            raise ValueError("Redis password is required")
        if cls.PORT < 1 or cls.PORT > 65535:
            raise ValueError("Invalid Redis port")
        if cls.TTL < 1:
            raise ValueError("TTL must be positive")

class EncryptionConfig:
    ENCRYPTION_KEY: str = os.getenv('ENCRYPTION_KEY')
    ALGORITHM: str = "AES-256-GCM"
    KEY_DERIVATION: str = "PBKDF2"
    ITERATIONS: int = 100000
    SALT_LENGTH: int = 16
    TAG_LENGTH: int = 16
    NONCE_LENGTH: int = 12
    
    @classmethod
    def validate(cls):
        """Validate encryption configuration"""
        if not cls.ENCRYPTION_KEY:
            raise ValueError("Encryption key is required")
        if len(cls.ENCRYPTION_KEY) < 32:
            raise ValueError("Encryption key must be at least 32 bytes")

# Validate configurations
validate_env_vars()
RedisConfig.validate()
EncryptionConfig.validate() 