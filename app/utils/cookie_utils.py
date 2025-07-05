from fastapi import Response
from app.core.config import settings
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    access_token_expires: Optional[int] = None,
    refresh_token_expires: Optional[int] = None
) -> Response:
    """
    Set authentication cookies with proper security settings
    
    Args:
        response: FastAPI Response object
        access_token: JWT access token
        refresh_token: JWT refresh token
        access_token_expires: Access token expiration time in seconds
        refresh_token_expires: Refresh token expiration time in seconds
    """
    
    # Calculate expiration times
    if access_token_expires is None:
        access_token_expires = settings.access_token_expire_minutes * 60
    
    if refresh_token_expires is None:
        refresh_token_expires = settings.refresh_token_expire_days * 24 * 60 * 60
    
    # Set access token cookie
    response.set_cookie(
        key=settings.access_token_cookie_name,
        value=access_token,
        max_age=access_token_expires,
        domain=settings.cookie_domain,
        secure=settings.cookie_secure,
        httponly=settings.cookie_httponly,
        samesite=settings.cookie_samesite,
        path="/"
    )
    
    # Set refresh token cookie
    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=refresh_token,
        max_age=refresh_token_expires,
        domain=settings.cookie_domain,
        secure=settings.cookie_secure,
        httponly=settings.cookie_httponly,
        samesite=settings.cookie_samesite,
        path="/"
    )
    
    logger.info("Authentication cookies set successfully")
    return response

def clear_auth_cookies(response: Response) -> Response:
    """
    Clear authentication cookies
    
    Args:
        response: FastAPI Response object
    """
    
    # Clear access token cookie
    response.delete_cookie(
        key=settings.access_token_cookie_name,
        domain=settings.cookie_domain,
        path="/"
    )
    
    # Clear refresh token cookie
    response.delete_cookie(
        key=settings.refresh_token_cookie_name,
        domain=settings.cookie_domain,
        path="/"
    )
    
    logger.info("Authentication cookies cleared successfully")
    return response

def set_cookie_with_options(
    response: Response,
    key: str,
    value: str,
    max_age: Optional[int] = None,
    domain: Optional[str] = None,
    secure: Optional[bool] = None,
    httponly: Optional[bool] = None,
    samesite: Optional[str] = None,
    path: str = "/"
) -> Response:
    """
    Set a cookie with custom options
    
    Args:
        response: FastAPI Response object
        key: Cookie name
        value: Cookie value
        max_age: Cookie max age in seconds
        domain: Cookie domain
        secure: Whether cookie is secure
        httponly: Whether cookie is httpOnly
        samesite: SameSite attribute
        path: Cookie path
    """
    
    # Use default settings if not provided
    if domain is None:
        domain = settings.cookie_domain
    if secure is None:
        secure = settings.cookie_secure
    if httponly is None:
        httponly = settings.cookie_httponly
    if samesite is None:
        samesite = settings.cookie_samesite
    
    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        domain=domain,
        secure=secure,
        httponly=httponly,
        samesite=samesite,
        path=path
    )
    
    return response 