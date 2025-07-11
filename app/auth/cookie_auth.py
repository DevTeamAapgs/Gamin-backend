from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Union
from app.auth.token_manager import token_manager
from app.core.config import settings
import logging

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
) -> dict:
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
    
    return payload

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
    
    # Check if user is admin (this would need to be implemented based on your user model)
    # For now, we'll assume the payload contains admin information
    if not payload.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return payload 