from fastapi import Request, Query, HTTPException, Depends, Header
from typing import Optional, Dict, Any, Union
from app.utils.enhanced_crypto import enhanced_crypto
import logging

logger = logging.getLogger(__name__)

async def decrypt_request_body(request: Request) -> Dict[str, Any]:
    """Decrypt entire request body."""
    try:
        body = await request.json()
        decrypted_body = {}
        
        for key, value in body.items():
            if isinstance(value, str):
                try:
                    decrypted_value = enhanced_crypto.decrypt_aes256(value)
                    decrypted_body[key] = decrypted_value
                except Exception as e:
                    logger.warning(f"Failed to decrypt field '{key}': {e}")
                    decrypted_body[key] = value  # Keep original if decryption fails
            else:
                decrypted_body[key] = value
        
        return decrypted_body
        
    except Exception as e:
        logger.error(f"Request body decryption failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid encrypted request body")

async def decrypt_selective_body(request: Request, encrypted_fields: list) -> Dict[str, Any]:
    """Decrypt only specific fields in request body."""
    try:
        body = await request.json()
        decrypted_body = body.copy()
        
        for field in encrypted_fields:
            if field in body and isinstance(body[field], str):
                try:
                    decrypted_body[field] = enhanced_crypto.decrypt_aes256(body[field])
                except Exception as e:
                    logger.warning(f"Failed to decrypt field '{field}': {e}")
                    # Keep original value if decryption fails
        
        return decrypted_body
        
    except Exception as e:
        logger.error(f"Selective decryption failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid encrypted data")

def decrypt_query_param(param: str = Query(..., description="Encrypted query parameter")) -> str:
    """Decrypt a single query parameter."""
    try:
        result = enhanced_crypto.decrypt_aes256(param)
        if isinstance(result, dict):
            raise ValueError("Query parameter cannot be a dictionary")
        return str(result)
    except Exception as e:
        logger.error(f"Query parameter decryption failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid encrypted query parameter")

def decrypt_header_param(param: str = Header(..., description="Encrypted header parameter")) -> str:
    """Decrypt a single header parameter."""
    try:
        result = enhanced_crypto.decrypt_aes256(param)
        if isinstance(result, dict):
            raise ValueError("Header parameter cannot be a dictionary")
        return str(result)
    except Exception as e:
        logger.error(f"Header parameter decryption failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid encrypted header parameter")

async def decrypt_game_data(request: Request) -> Dict[str, Any]:
    """Decrypt game-specific data (score, moves, etc.)."""
    encrypted_fields = ["score", "moves", "game_state", "player_actions"]
    return await decrypt_selective_body(request, encrypted_fields)

async def decrypt_payment_data(request: Request) -> Dict[str, Any]:
    """Decrypt payment-related data."""
    encrypted_fields = ["amount", "wallet_address", "transaction_id", "payment_method"]
    return await decrypt_selective_body(request, encrypted_fields)

async def decrypt_user_data(request: Request) -> Dict[str, Any]:
    """Decrypt user-sensitive data."""
    encrypted_fields = ["email", "phone", "personal_info", "preferences"]
    return await decrypt_selective_body(request, encrypted_fields)

# Convenience functions for common scenarios
def decrypt_score(score: str = Query(..., description="Encrypted game score")) -> Union[int, float]:
    """Decrypt and validate game score."""
    try:
        result = enhanced_crypto.decrypt_aes256(score)
        if isinstance(result, dict):
            raise ValueError("Score cannot be a dictionary")
        
        decrypted = str(result)
        # Try to convert to number
        try:
            return int(decrypted)
        except ValueError:
            return float(decrypted)
    except Exception as e:
        logger.error(f"Score decryption failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid encrypted score")

def decrypt_wallet_address(address: str = Query(..., description="Encrypted wallet address")) -> str:
    """Decrypt wallet address."""
    try:
        result = enhanced_crypto.decrypt_aes256(address)
        if isinstance(result, dict):
            raise ValueError("Wallet address cannot be a dictionary")
        
        decrypted = str(result)
        # Basic validation for wallet address format
        if not decrypted.startswith("0x") or len(decrypted) != 42:
            raise ValueError("Invalid wallet address format")
        return decrypted
    except Exception as e:
        logger.error(f"Wallet address decryption failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid encrypted wallet address") 