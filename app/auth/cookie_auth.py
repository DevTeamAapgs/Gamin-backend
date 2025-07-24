from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Union
from app.auth.token_manager import token_manager
from app.core.config import settings
from app.models.player import Player
from app.db.mongo import get_database
from app.core.enums import PlayerType
from bson import ObjectId
import logging
from app.utils.crypto import AESCipher
from app.utils.crypto_dependencies import get_crypto_service
from app.models.game import GemType
import json
from app.utils.crypto import AESCipher

from app.schemas.player import PlayerInfoSchema

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

class CookieAuth:
    """Cookie-based authentication with fallback to Bearer token"""
    
    def __init__(self):
        self.access_token_cookie_name = settings.access_token_cookie_name
        self.refresh_token_cookie_name = settings.refresh_token_cookie_name
    
    def get_token_from_cookies(self, request: Request) -> Optional[str]:
        """Extract access token from cookies"""
      
        return request.cookies.get(self.access_token_cookie_name)
    
    def get_refresh_token_from_cookies(self, request: Request) -> Optional[str]:
        """Extract refresh token from cookies"""
        return request.cookies.get(self.refresh_token_cookie_name)
    
    def get_token_from_header(self, credentials: Optional[HTTPAuthorizationCredentials]) -> Optional[str]:
        """Extract token from Authorization header"""
        if credentials:
            return credentials.credentials
        return None
    
    def get_token(self, request: Request, credentials: Optional[HTTPAuthorizationCredentials] = None) -> Optional[str]:
        """Get token from cookies first, then fallback to header"""
        # Try cookies first
        token = self.get_token_from_cookies(request)
        # print(token,"token")
        if token:
            return token
        
        # Fallback to header
        return self.get_token_from_header(credentials)
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify the token and return payload"""
        if not token:
            return None
        
        try:
            payload = token_manager.verify_token(token)
            return payload
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None

cookie_auth = CookieAuth()

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> PlayerInfoSchema:
    """Get current user from token (cookie or header)"""
    token = cookie_auth.get_token(request, credentials)
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = cookie_auth.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user ID from payload
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch player from database
    db = get_database()
    player_doc = await db.players.find_one({"_id": ObjectId(user_id)})
    
    if not player_doc:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    crypto = get_crypto_service()
    # Safely handle decryption only if value is a string
    for field in ["token_balance", "total_tokens_earned", "total_tokens_spent"]:
        value = player_doc.get(field, "0")
        if isinstance(value, str):
            try:
                player_doc[field] = float(crypto.decrypt(value))
            except Exception:
                player_doc[field] = 0.0
        else:
            player_doc[field] = float(value)
    # Decrypt gems
    gems_value = player_doc.get("gems", {})
    if isinstance(gems_value, dict):
        decrypted_gems = {}
        for color in ["blue", "green", "red"]:
            val = gems_value.get(color, "0")
            if isinstance(val, str):
                try:
                    decrypted_gems[color] = int(crypto.decrypt(val))
                except Exception:
                    decrypted_gems[color] = 0
            else:
                decrypted_gems[color] = int(val)
        player_doc["gems"] = GemType(**decrypted_gems)
    else:
        player_doc["gems"] = GemType(blue=0, green=0, red=0)
    print("Decrypted player_doc:", player_doc)
    if not player_doc:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Convert to Player object
    player_doc["id"] = str(player_doc["_id"])
    return PlayerInfoSchema(**player_doc)

async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """Get current user from token (cookie or header) - optional authentication"""
    token = cookie_auth.get_token(request, credentials)
    
    if not token:
        return None
    
    payload = cookie_auth.verify_token(token)
    return payload

async def verify_admin(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """Verify admin access from token (cookie or header)"""
    token = cookie_auth.get_token(request, credentials)
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = cookie_auth.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user ID from payload and fetch full user document
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database and check current playertype (not from token)
    db = get_database()
    user_doc = await db.players.find_one({"_id": ObjectId(user_id)})
    
    if not user_doc:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is admin (playertype=0 for SUPERADMIN, 1 for ADMINEMPLOYEE)
    if user_doc.get("player_type") not in [PlayerType.SUPERADMIN, PlayerType.ADMINEMPLOYEE]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return user_doc 