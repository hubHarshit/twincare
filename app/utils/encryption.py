from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
import base64
import os
import json
from typing import Tuple
from ..config.redis_config import EncryptionConfig

class EncryptionService:
    def __init__(self):
        if not EncryptionConfig.ENCRYPTION_KEY:
            raise ValueError("Encryption key not set in environment variables")
        self.key = self._derive_key(EncryptionConfig.ENCRYPTION_KEY.encode())
        self.cipher = AESGCM(self.key)
        self._load_or_create_salt()

    def _load_or_create_salt(self):
        """Load or create a new salt for key derivation"""
        salt_file = "salt.key"
        if os.path.exists(salt_file):
            with open(salt_file, "rb") as f:
                self.salt = f.read()
        else:
            self.salt = os.urandom(EncryptionConfig.SALT_LENGTH)
            with open(salt_file, "wb") as f:
                f.write(self.salt)

    def _derive_key(self, password: bytes) -> bytes:
        """Derive a key using PBKDF2 with stored salt"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=EncryptionConfig.ITERATIONS,
        )
        return base64.urlsafe_b64encode(kdf.derive(password))

    def encrypt(self, data: str) -> str:
        """Encrypt data for storage with error handling"""
        try:
            nonce = os.urandom(EncryptionConfig.NONCE_LENGTH)
            ciphertext = self.cipher.encrypt(nonce, data.encode(), None)
            return base64.b64encode(nonce + ciphertext).decode('utf-8')
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {str(e)}")

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt stored data with error handling"""
        try:
            raw_data = base64.b64decode(encrypted_data.encode('utf-8'))
            nonce = raw_data[:EncryptionConfig.NONCE_LENGTH]
            ciphertext = raw_data[EncryptionConfig.NONCE_LENGTH:]
            return self.cipher.decrypt(nonce, ciphertext, None).decode('utf-8')
        except InvalidTag:
            raise EncryptionError("Data integrity check failed")
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {str(e)}")

class EncryptionError(Exception):
    """Custom exception for encryption/decryption errors"""
    pass 