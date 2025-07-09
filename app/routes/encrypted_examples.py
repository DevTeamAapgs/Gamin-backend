from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Union
from app.utils.enhanced_crypto import enhanced_crypto
from app.utils.enhanced_crypto_dependencies import (
    decrypt_request_body,
    decrypt_selective_body,
    decrypt_query_param,
    decrypt_score,
    decrypt_wallet_address,
    decrypt_game_data,
    decrypt_payment_data,
    decrypt_user_data
)
from app.middleware.enhanced_encryption_middleware import (
    EnhancedEncryptedJSONResponse,
    encrypt_sensitive_response,
    encrypt_game_response,
    encrypt_payment_response,
    encrypt_user_response,
    encrypt_entire_response
)
from app.auth.cookie_auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/encrypted", tags=["Encrypted Examples"])

# Example 1: Basic encryption/decryption
@router.post("/basic")
async def basic_encryption_example():
    """Basic encryption/decryption example."""
    # Encrypt some data
    original_data = "sensitive_game_score_1500"
    encrypted = enhanced_crypto.encrypt_aes256(original_data)
    decrypted = enhanced_crypto.decrypt_aes256(encrypted)
    
    return {
        "original": original_data,
        "encrypted": encrypted,
        "decrypted": decrypted,
        "success": original_data == decrypted
    }

# Example 2: Object encryption
@router.post("/object")
async def object_encryption_example():
    """Encrypt/decrypt Python objects."""
    game_data = {
        "player_id": "12345",
        "score": 1500,
        "level": 5,
        "moves": ["up", "down", "left", "right"],
        "secret_key": "abc123"
    }
    
    # Encrypt object
    encrypted_object = enhanced_crypto.encrypt_object(game_data)
    decrypted_object = enhanced_crypto.decrypt_object(encrypted_object)
    
    return {
        "original": game_data,
        "encrypted": encrypted_object,
        "decrypted": decrypted_object,
        "success": game_data == decrypted_object
    }

# Example 3: Encrypted request body
@router.post("/request-body")
async def encrypted_request_body_example(decrypted_body: Dict[str, Any] = Depends(decrypt_request_body)):
    """Handle encrypted request body."""
    return {
        "message": "Received encrypted data",
        "decrypted_data": decrypted_body,
        "data_type": type(decrypted_body).__name__
    }

# Example 4: Selective field decryption
@router.post("/selective-decryption")
async def selective_decryption_example(decrypted_data: Dict[str, Any] = Depends(decrypt_game_data)):
    """Decrypt only game-specific fields."""
    return {
        "message": "Game data decrypted",
        "decrypted_game_data": decrypted_data
    }

# Example 5: Encrypted query parameters
@router.get("/query-param")
async def encrypted_query_example(decrypted_param: str = Depends(decrypt_query_param)):
    """Handle encrypted query parameter."""
    return {
        "message": "Query parameter decrypted",
        "decrypted_value": decrypted_param
    }

# Example 6: Encrypted score validation
@router.get("/score")
async def encrypted_score_example(score: Union[int, float] = Depends(decrypt_score)):
    """Handle encrypted game score with validation."""
    return {
        "message": "Score decrypted and validated",
        "score": score,
        "score_type": type(score).__name__
    }

# Example 7: Encrypted wallet address
@router.get("/wallet")
async def encrypted_wallet_example(wallet: str = Depends(decrypt_wallet_address)):
    """Handle encrypted wallet address with validation."""
    return {
        "message": "Wallet address decrypted and validated",
        "wallet_address": wallet
    }

# Example 8: Encrypted response with sensitive fields
@router.get("/sensitive-response")
async def sensitive_response_example():
    """Return response with encrypted sensitive fields."""
    sensitive_data = {
        "user_id": "12345",
        "username": "player123",
        "password": "secret_password_123",
        "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
        "token_balance": 1000,
        "email": "player@example.com"
    }
    
    return encrypt_sensitive_response(sensitive_data)

# Example 9: Game-specific encrypted response
@router.get("/game-response")
async def game_response_example():
    """Return game data with encrypted sensitive game fields."""
    game_data = {
        "game_id": "game_123",
        "player_id": "player_456",
        "score": 1500,
        "moves": ["up", "down", "left"],
        "game_state": "active",
        "secret_key": "game_secret_789",
        "public_info": "This is public game info"
    }
    
    return encrypt_game_response(game_data)

# Example 10: Payment encrypted response
@router.get("/payment-response")
async def payment_response_example():
    """Return payment data with encrypted sensitive payment fields."""
    payment_data = {
        "transaction_id": "txn_123",
        "amount": 100.50,
        "wallet_address": "0xabcdef1234567890abcdef1234567890abcdef12",
        "payment_method": "crypto",
        "status": "completed",
        "public_info": "Payment processed successfully"
    }
    
    return encrypt_payment_response(payment_data)

# Example 11: User data encrypted response
@router.get("/user-response")
async def user_response_example():
    """Return user data with encrypted sensitive user fields."""
    user_data = {
        "user_id": "user_123",
        "username": "john_doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "personal_info": "Some personal details",
        "preferences": {"theme": "dark", "language": "en"},
        "public_profile": "Public profile information"
    }
    
    return encrypt_user_response(user_data)

# Example 12: Entire response encryption
@router.get("/full-encryption")
async def full_encryption_example():
    """Return entirely encrypted response."""
    complete_data = {
        "message": "This entire response is encrypted",
        "data": {
            "sensitive": "very_sensitive_data",
            "public": "public_data"
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }
    
    return encrypt_entire_response(complete_data)

# Example 13: Real-world game submission with encryption
@router.post("/game-submission")
async def game_submission_example(
    game_data: Dict[str, Any] = Depends(decrypt_game_data),
    current_user: dict = Depends(get_current_user)
):
    """Real-world example: Handle encrypted game submission."""
    try:
        # Extract decrypted game data
        score = game_data.get("score")
        moves = game_data.get("moves", [])
        game_state = game_data.get("game_state")
        
        # Process game submission
        processed_data = {
            "player_id": current_user.get("sub"),
            "score": score,
            "moves_count": len(moves),
            "game_state": game_state,
            "submission_time": "2024-01-01T00:00:00Z",
            "status": "processed"
        }
        
        # Return encrypted response
        return encrypt_game_response(processed_data)
        
    except Exception as e:
        logger.error(f"Game submission failed: {e}")
        raise HTTPException(status_code=500, detail="Game submission failed")

# Example 14: Payment processing with encryption
@router.post("/payment-processing")
async def payment_processing_example(
    payment_data: Dict[str, Any] = Depends(decrypt_payment_data),
    current_user: dict = Depends(get_current_user)
):
    """Real-world example: Handle encrypted payment data."""
    try:
        # Extract decrypted payment data
        amount = payment_data.get("amount")
        wallet_address = payment_data.get("wallet_address")
        payment_method = payment_data.get("payment_method")
        
        # Process payment
        transaction_result = {
            "transaction_id": f"txn_{enhanced_crypto.generate_secure_token(16)}",
            "player_id": current_user.get("sub"),
            "amount": amount,
            "wallet_address": wallet_address,
            "payment_method": payment_method,
            "status": "completed",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        # Return encrypted response
        return encrypt_payment_response(transaction_result)
        
    except Exception as e:
        logger.error(f"Payment processing failed: {e}")
        raise HTTPException(status_code=500, detail="Payment processing failed")

# Example 15: Secure token generation
@router.get("/secure-token")
async def secure_token_example():
    """Generate secure tokens for various purposes."""
    tokens = {
        "game_token": enhanced_crypto.generate_secure_token(32),
        "session_token": enhanced_crypto.generate_secure_token(64),
        "api_key": enhanced_crypto.generate_secure_token(128)
    }
    
    return encrypt_sensitive_response(tokens, ["game_token", "session_token", "api_key"])

# Example 16: Data hashing for storage
@router.post("/hash-data")
async def hash_data_example():
    """Hash sensitive data for secure storage."""
    sensitive_data = "player_secret_password_123"
    hashed_data = enhanced_crypto.hash_sensitive_data(sensitive_data)
    
    # Verify hash
    is_valid = enhanced_crypto.verify_hash(sensitive_data, hashed_data)
    
    return {
        "original_data": sensitive_data,
        "hashed_data": hashed_data,
        "verification": is_valid
    } 