import base64
import os
import json
import logging
from typing import Dict, Any, Optional, Union
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from hashlib import sha256, pbkdf2_hmac
from app.core.config import settings

logger = logging.getLogger(__name__)

class EnhancedCrypto:
    """Enhanced cryptography utilities for the gaming platform."""
    
    def __init__(self):
        self.secret_key = os.getenv("AES_SECRET_KEY", settings.aes_key)
        self.salt = os.getenv("CRYPTO_SALT", settings.salt)
        self.iterations = 100000
        
    def derive_key(self, secret: str, salt: Optional[str] = None) -> bytes:
        """Derive a key using PBKDF2."""
        salt_bytes = (salt or self.salt).encode()
        return pbkdf2_hmac('sha256', secret.encode(), salt_bytes, self.iterations)
    
    def encrypt_aes256(self, data: Union[str, dict], key: Optional[str] = None) -> str:
        """Encrypt data using AES-256-CBC."""
        try:
            # Convert dict to JSON string if needed
            if isinstance(data, dict):
                data = json.dumps(data)
            
            # Derive key
            encryption_key = self.derive_key(key or self.secret_key)
            
            # Generate random IV
            iv = get_random_bytes(16)
            
            # Create cipher
            cipher = AES.new(encryption_key, AES.MODE_CBC, iv)
            
            # Encrypt data
            padded_data = pad(data.encode('utf-8'), AES.block_size)
            encrypted_data = cipher.encrypt(padded_data)
            
            # Combine IV and encrypted data
            combined = iv + encrypted_data
            
            # Return base64 encoded string
            return base64.urlsafe_b64encode(combined).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError(f"Encryption failed: {str(e)}")
    
    def decrypt_aes256(self, encrypted_data: str, key: Optional[str] = None) -> Union[str, dict]:
        """Decrypt data using AES-256-CBC."""
        try:
            # Decode base64
            combined = base64.urlsafe_b64decode(encrypted_data)
            
            # Extract IV and encrypted data
            iv = combined[:16]
            encrypted = combined[16:]
            
            # Derive key
            decryption_key = self.derive_key(key or self.secret_key)
            
            # Create cipher
            cipher = AES.new(decryption_key, AES.MODE_CBC, iv)
            
            # Decrypt data
            decrypted_padded = cipher.decrypt(encrypted)
            decrypted_data = unpad(decrypted_padded, AES.block_size)
            
            # Convert to string
            result = decrypted_data.decode('utf-8')
            
            # Try to parse as JSON
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return result
                
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def encrypt_object(self, obj: Dict[str, Any], key: Optional[str] = None) -> str:
        """Encrypt a Python object (dict)."""
        return self.encrypt_aes256(obj, key)
    
    def decrypt_object(self, encrypted_data: str, key: Optional[str] = None) -> Dict[str, Any]:
        """Decrypt data back to a Python object (dict)."""
        result = self.decrypt_aes256(encrypted_data, key)
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                raise ValueError("Decrypted data is not a valid JSON object")
        return result
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a cryptographically secure random token."""
        return base64.urlsafe_b64encode(get_random_bytes(length)).decode('utf-8')
    
    def hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data for storage (one-way)."""
        return sha256(data.encode()).hexdigest()
    
    def verify_hash(self, data: str, hash_value: str) -> bool:
        """Verify data against its hash."""
        return self.hash_sensitive_data(data) == hash_value

# Global instance
enhanced_crypto = EnhancedCrypto() 