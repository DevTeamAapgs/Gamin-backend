from fastapi.responses import JSONResponse
from fastapi import Request, Response
from typing import Dict, Any, Optional, Union
from app.utils.enhanced_crypto import enhanced_crypto
import json
import logging

logger = logging.getLogger(__name__)

class EnhancedEncryptedJSONResponse(JSONResponse):
    """Enhanced encrypted JSON response with selective field encryption."""
    
    def __init__(
        self,
        content: Any,
        encrypt_fields: Optional[list] = None,
        encrypt_entire_response: bool = False,
        **kwargs
    ):
        self.encrypt_fields = encrypt_fields or []
        self.encrypt_entire_response = encrypt_entire_response
        super().__init__(content, **kwargs)
    
    def render(self, content) -> bytes:
        if self.encrypt_entire_response:
            # Encrypt the entire response
            encrypted_data = enhanced_crypto.encrypt_aes256(content)
            return super().render({"encrypted_data": encrypted_data})
        
        elif self.encrypt_fields:
            # Encrypt only specific fields
            if isinstance(content, dict):
                encrypted_content = content.copy()
                for field in self.encrypt_fields:
                    if field in encrypted_content:
                        try:
                            encrypted_content[field] = enhanced_crypto.encrypt_aes256(
                                str(encrypted_content[field])
                            )
                        except Exception as e:
                            logger.error(f"Failed to encrypt field '{field}': {e}")
                            # Keep original value if encryption fails
                
                return super().render(encrypted_content)
            else:
                return super().render(content)
        
        else:
            # No encryption
            return super().render(content)

class EncryptionMiddleware:
    """Middleware for automatic response encryption based on content type."""
    
    def __init__(self, app):
        self.app = app
        self.sensitive_patterns = [
            "password", "token", "secret", "key", "private",
            "wallet", "balance", "score", "personal", "email"
        ]
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Create a custom response handler
            original_send = send
            
            async def custom_send(message):
                if message["type"] == "http.response.body":
                    # Check if response contains sensitive data
                    if "body" in message:
                        try:
                            body = message["body"].decode()
                            data = json.loads(body)
                            
                            # Check for sensitive fields
                            if self._contains_sensitive_data(data):
                                # Encrypt sensitive fields
                                encrypted_data = self._encrypt_sensitive_fields(data)
                                message["body"] = json.dumps(encrypted_data).encode()
                        except Exception as e:
                            logger.warning(f"Failed to process response body: {e}")
                
                await original_send(message)
            
            await self.app(scope, receive, custom_send)
        else:
            await self.app(scope, receive, send)
    
    def _contains_sensitive_data(self, data: Any) -> bool:
        """Check if data contains sensitive information."""
        if isinstance(data, dict):
            for key, value in data.items():
                key_lower = str(key).lower()
                if any(pattern in key_lower for pattern in self.sensitive_patterns):
                    return True
                if isinstance(value, (dict, list)):
                    if self._contains_sensitive_data(value):
                        return True
        elif isinstance(data, list):
            for item in data:
                if self._contains_sensitive_data(item):
                    return True
        return False
    
    def _encrypt_sensitive_fields(self, data: Any) -> Any:
        """Encrypt sensitive fields in the data."""
        if isinstance(data, dict):
            encrypted_data = {}
            for key, value in data.items():
                key_lower = str(key).lower()
                if any(pattern in key_lower for pattern in self.sensitive_patterns):
                    try:
                        encrypted_data[key] = enhanced_crypto.encrypt_aes256(str(value))
                    except Exception as e:
                        logger.error(f"Failed to encrypt field '{key}': {e}")
                        encrypted_data[key] = value  # Keep original if encryption fails
                elif isinstance(value, (dict, list)):
                    encrypted_data[key] = self._encrypt_sensitive_fields(value)
                else:
                    encrypted_data[key] = value
            return encrypted_data
        elif isinstance(data, list):
            return [self._encrypt_sensitive_fields(item) for item in data]
        else:
            return data

# Utility functions for common encryption scenarios
def encrypt_sensitive_response(content: Dict[str, Any], sensitive_fields: Optional[list] = None) -> EnhancedEncryptedJSONResponse:
    """Create a response with encrypted sensitive fields."""
    if sensitive_fields is None:
        sensitive_fields = ["password", "token", "secret", "wallet_address", "balance"]
    
    return EnhancedEncryptedJSONResponse(
        content=content,
        encrypt_fields=sensitive_fields
    )

def encrypt_game_response(content: Dict[str, Any]) -> EnhancedEncryptedJSONResponse:
    """Create a response with encrypted game-specific sensitive data."""
    game_sensitive_fields = ["score", "moves", "game_state", "player_actions", "secret_key"]
    return encrypt_sensitive_response(content, game_sensitive_fields)

def encrypt_payment_response(content: Dict[str, Any]) -> EnhancedEncryptedJSONResponse:
    """Create a response with encrypted payment-related sensitive data."""
    payment_sensitive_fields = ["amount", "wallet_address", "transaction_id", "payment_method"]
    return encrypt_sensitive_response(content, payment_sensitive_fields)

def encrypt_user_response(content: Dict[str, Any]) -> EnhancedEncryptedJSONResponse:
    """Create a response with encrypted user-sensitive data."""
    user_sensitive_fields = ["email", "phone", "personal_info", "preferences"]
    return encrypt_sensitive_response(content, user_sensitive_fields)

def encrypt_entire_response(content: Any) -> EnhancedEncryptedJSONResponse:
    """Create a response with the entire content encrypted."""
    return EnhancedEncryptedJSONResponse(
        content=content,
        encrypt_entire_response=True
    ) 