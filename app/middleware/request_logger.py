from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import time
from typing import Callable
import hashlib
import json
from app.services.logging_service import logging_service
from app.auth.token_manager import token_manager

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, exclude_paths: list = None, enable_db_logging: bool = True):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]
        self.enable_db_logging = enable_db_logging
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        start_time = time.time()
        
        # Extract client information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        device_fingerprint = self._generate_device_fingerprint(request)
        
        # Extract player ID from token if available
        player_id = None
        try:
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                payload = token_manager.verify_token(token)
                if payload:
                    player_id = payload.get("sub")
        except Exception:
            pass  # Ignore token parsing errors
        
        # Log request start
        logger.info(f"Request started: {request.method} {request.url.path} from {client_ip}")
        
        # Prepare request data for database logging
        request_data = {
            "method": request.method,
            "path": request.url.path,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "device_fingerprint": device_fingerprint,
            "player_id": player_id,
            "request_headers": dict(request.headers),
            "request_body": None  # Don't log request body for security
        }
        
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Update request data with response info
            request_data.update({
                "status_code": response.status_code,
                "response_headers": dict(response.headers),
                "process_time": process_time,
                "error_message": None
            })
            
            # Log request completion
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"Status: {response.status_code} "
                f"Time: {process_time:.3f}s "
                f"IP: {client_ip} "
                f"Device: {device_fingerprint[:8]}"
            )
            
            # Log to database if enabled
            if self.enable_db_logging:
                await logging_service.log_request(request_data)
            
            # Add headers for client tracking
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Device-Fingerprint"] = device_fingerprint
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # Update request data with error info
            request_data.update({
                "status_code": 500,
                "process_time": process_time,
                "error_message": str(e)
            })
            
            # Log request failure
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"Error: {str(e)} "
                f"Time: {process_time:.3f}s "
                f"IP: {client_ip}"
            )
            
            # Log to database if enabled
            if self.enable_db_logging:
                await logging_service.log_request(request_data)
            
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers (common with proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    def _generate_device_fingerprint(self, request: Request) -> str:
        """Generate device fingerprint from request headers."""
        fingerprint_data = {
            "user_agent": request.headers.get("user-agent", ""),
            "accept_language": request.headers.get("accept-language", ""),
            "accept_encoding": request.headers.get("accept-encoding", ""),
            "sec_ch_ua": request.headers.get("sec-ch-ua", ""),
            "sec_ch_ua_platform": request.headers.get("sec-ch-ua-platform", ""),
            "sec_ch_ua_mobile": request.headers.get("sec-ch-ua-mobile", ""),
        }
        
        # Create hash from fingerprint data
        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Add security headers
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        
        
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/ https://fastapi.tiangolo.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/; "
            "img-src 'self' data: https://fastapi.tiangolo.com; "
            "font-src 'self' https://cdn.jsdelivr.net https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/;"
        )


        return response

class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log security events to database."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Log suspicious activities
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        device_fingerprint = self._generate_device_fingerprint(request)
        
        # Check for suspicious patterns
        if await self._is_suspicious_request(request, client_ip):
            await logging_service.log_security_event({
                "event_type": "suspicious_activity",
                "client_ip": client_ip,
                "device_fingerprint": device_fingerprint,
                "user_agent": user_agent,
                "details": {
                    "path": request.url.path,
                    "method": request.method,
                    "reason": "Suspicious request pattern detected"
                },
                "severity": "warning"
            })
        
        response = await call_next(request)
        
        # Log failed authentication attempts
        if response.status_code == 401:
            await logging_service.log_security_event({
                "event_type": "failed_login",
                "client_ip": client_ip,
                "device_fingerprint": device_fingerprint,
                "user_agent": user_agent,
                "details": {
                    "path": request.url.path,
                    "method": request.method
                },
                "severity": "warning"
            })
        
        return response
    
    async def _is_suspicious_request(self, request: Request, client_ip: str) -> bool:
        """Check if request is suspicious."""
        # Check for rapid requests (rate limiting)
        # Check for unusual user agents
        # Check for known malicious patterns
        # This is a simplified implementation
        
        suspicious_patterns = [
            "/admin", "/wp-admin", "/phpmyadmin", "/.env",
            "sqlmap", "nmap", "nikto", "dirb"
        ]
        
        path = request.url.path.lower()
        user_agent = request.headers.get("user-agent", "").lower()
        
        # Check for suspicious paths
        for pattern in suspicious_patterns:
            if pattern in path:
                return True
        
        # Check for suspicious user agents
        suspicious_agents = ["sqlmap", "nmap", "nikto", "dirb", "wget", "curl"]
        for agent in suspicious_agents:
            if agent in user_agent:
                return True
        
        return False
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _generate_device_fingerprint(self, request: Request) -> str:
        """Generate device fingerprint from request headers."""
        fingerprint_data = {
            "user_agent": request.headers.get("user-agent", ""),
            "accept_language": request.headers.get("accept-language", ""),
            "accept_encoding": request.headers.get("accept-encoding", ""),
        }
        
        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest() 