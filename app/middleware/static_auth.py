# middleware/static_auth.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from typing import Callable, Iterable
from app.auth.cookie_auth import CookieAuth

cookie_auth = CookieAuth()

class StaticAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, protected_prefixes: Iterable[str] = ("/public/game/",)):
        super().__init__(app)
        self.protected_prefixes = tuple(protected_prefixes)

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path

        # Allow CORS preflight through
        if request.method == "OPTIONS":
            return await call_next(request)

        # Gate only the protected static prefixes
        if any(path.startswith(p) for p in self.protected_prefixes):
            token =  cookie_auth.get_token(request)
            if not token:
                return JSONResponse({"detail": "Not authenticated"}, status_code=401)
            try:
                claims = cookie_auth.verify_token(token)
                if not claims:
                    return JSONResponse({"detail": "Invalid or expired token"}, status_code=401)
                request.state.user = claims  # optional, for downstream
            except Exception as e:
                return JSONResponse({"detail": "Invalid or expired token"}, status_code=401)

        return await call_next(request)
