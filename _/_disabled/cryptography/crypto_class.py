"""
Encryption utility for database credentials
Uses Fernet symmetric encryption from cryptography library
"""

import base64
import logging
from typing import Any, Dict, Optional, Union
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import config


class CredentialCipher:
    """Handles encryption and decryption of database credentials"""
    
    # Fields that should be encrypted
    ENCRYPTED_FIELDS = {'password', 'api_key', 'secret', 'token', 'private_key'}
    
    def __init__(self):
        self.logger = logging.getLogger('credential_cipher')
        self._cipher = None
        self._init_cipher()
    
    def _init_cipher(self):
        """Initialize the Fernet cipher with the key from config"""
        try:
            cipher_key = config.get('DB_CIPHER_KEY')
            if not cipher_key:
                self.logger.error("DB_CIPHER_KEY not found in config")
                raise ValueError("DB_CIPHER_KEY not configured")
            
            # Ensure the key is properly formatted
            if isinstance(cipher_key, str):
                cipher_key = cipher_key.encode('utf-8')
            
            # If the key is not a valid Fernet key, derive one from it
            try:
                self._cipher = Fernet(cipher_key)
            except Exception:
                # Key is not a valid Fernet key, derive one
                self.logger.info("Deriving Fernet key from DB_CIPHER_KEY")
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b'stable_salt',  # Using stable salt for consistent key derivation
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(cipher_key))
                self._cipher = Fernet(key)
            
            self.logger.info("Credential cipher initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize cipher: {e}")
            raise
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt a single string value"""
        if not value:
            return value
        
        try:
            encrypted = self._cipher.encrypt(value.encode('utf-8'))
            # Return as base64 string for JSON storage
            return base64.urlsafe_b64encode(encrypted).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a single encrypted value"""
        if not encrypted_value:
            return encrypted_value
        
        try:
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode('utf-8'))
            decrypted = self._cipher.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except InvalidToken:
            self.logger.error("Invalid token - wrong key or corrupted data")
            raise ValueError("Failed to decrypt: invalid key or corrupted data")
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_dict(self, data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Encrypt sensitive fields in a dictionary"""
        if not data:
            return data
        
        encrypted_data = data.copy()
        
        for field, value in data.items():
            if field.lower() in self.ENCRYPTED_FIELDS and isinstance(value, str):
                try:
                    encrypted_data[field] = self.encrypt_value(value)
                    self.logger.debug(f"Encrypted field: {field}")
                except Exception as e:
                    self.logger.error(f"Failed to encrypt field {field}: {e}")
                    raise
        
        return encrypted_data
    
    def decrypt_dict(self, data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Decrypt sensitive fields in a dictionary"""
        if not data:
            return data
        
        decrypted_data = data.copy()
        
        for field, value in data.items():
            if field.lower() in self.ENCRYPTED_FIELDS and isinstance(value, str):
                try:
                    decrypted_data[field] = self.decrypt_value(value)
                    self.logger.debug(f"Decrypted field: {field}")
                except Exception as e:
                    self.logger.error(f"Failed to decrypt field {field}: {e}")
                    raise
        
        return decrypted_data
    
    def is_encrypted(self, value: str) -> bool:
        """Check if a value appears to be encrypted"""
        if not value:
            return False
        
        try:
            # Try to decode as base64
            decoded = base64.urlsafe_b64decode(value.encode('utf-8'))
            # Check if it looks like Fernet token (starts with version byte)
            return len(decoded) > 0 and decoded[0:1] == b'\x80'
        except Exception:
            return False


# Global cipher instance
_cipher_instance = None


def get_cipher() -> CredentialCipher:
    """Get or create the global cipher instance"""
    global _cipher_instance
    if _cipher_instance is None:
        _cipher_instance = CredentialCipher()
    return _cipher_instance