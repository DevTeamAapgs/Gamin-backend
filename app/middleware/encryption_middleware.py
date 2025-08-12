import time
import logging
import json
from typing import Tuple, List, Dict
from fastapi.responses import FileResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.utils.crypto import AESCipher  # your AES util

logger = logging.getLogger("middleware")
logger.setLevel(logging.INFO)

# Paths and content types to skip encryption for
BYPASS_PATH_PREFIXES = (
    "/public/",
    "/static/",
    "/assets/",
)
BYPASS_EXACT_PATHS = {
    "/openapi.json", "/docs", "/redoc",
    "/.well-known/appspecific/com.chrome.devtools.json",
}
BYPASS_CONTENT_TYPES = (
    "application/manifest+json",  # PWA manifest
    "text/html",
    "text/css",
    "text/javascript",
    "application/javascript",
    "application/x-javascript",
    "image/",
    "audio/",
    "video/",
    "font/",
    "application/octet-stream",
)

class ResponseEncryptionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, crypto: AESCipher):
        super().__init__(app)
        self.crypto = crypto

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        path = request.url.path
        print("CHECKING 0" ,f"{request.method} {path}")
        # Call downstream
        response = await call_next(request)
        print(response)
        if path.startswith(BYPASS_PATH_PREFIXES):
            print("CHECKING 5" ,f"{request.method} {path}")
            return response

        # Path or header-based bypass
        if (
            path in BYPASS_EXACT_PATHS
            or path.startswith(BYPASS_PATH_PREFIXES)
            or request.headers.get("x-plaintext", "").lower() == "true"
        ):
            print("CHECKING 4" ,f"{request.method} {path}")        
            return response

        

        # Don’t encrypt non-200
        if response.status_code != 200:
            print("CHECKING 3" ,f"{request.method} {path}")
            return response

        content_type = (response.headers.get("content-type") or "").lower()

        # Skip for bypassed content types
        if any(content_type.startswith(ct) for ct in BYPASS_CONTENT_TYPES):
            print("CHECKING 2" ,f"{request.method} {path}")
            return response

        # Skip for file/stream responses
        if isinstance(response, (FileResponse, StreamingResponse)):
            print("CHECKING 1" ,f"{request.method} {path}")
            return response

        # Only encrypt JSON API responses
        if not content_type.startswith("application/json"):
            return response
        print("Encrypting response" ,f"{request.method} {path}")
        try:
            # Drain original body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            original_text = body.decode("utf-8")
            encrypted = self.crypto.encrypt(original_text)
            encrypted_body = json.dumps({"data": encrypted}).encode("utf-8")

            elapsed = time.time() - start_time
            logger.info(
                f"[EncryptMiddleware] {request.method} {path} | {len(original_text)} bytes | {elapsed:.4f}s"
            )

            return self._rebuild_response(encrypted_body, response, "application/json")

        except Exception as e:
            logger.exception("Encryption failed")
            err = json.dumps({"error": f"Encryption failed: {str(e)}"}).encode("utf-8")
            return self._rebuild_response(err, response, "application/json", status_code=500)

    def _rebuild_response(
        self,
        body: bytes,
        original_response: Response,
        media_type: str,
        status_code: int | None = None,
    ) -> Response:
        normal_headers, set_cookie_headers = self._split_set_cookie_headers(original_response.raw_headers)
        normal_headers.pop("content-length", None)  # Recalculate

        new_response = Response(
            content=body,
            status_code=status_code or original_response.status_code,
            headers=normal_headers,
            media_type=media_type,
            background=original_response.background,
        )

        # Re-attach Set-Cookie headers
        for set_cookie in set_cookie_headers:
            new_response.raw_headers.append((b"set-cookie", set_cookie))

        return new_response

    def _split_set_cookie_headers(
        self, raw_headers: List[Tuple[bytes, bytes]]
    ) -> Tuple[Dict[str, str], List[bytes]]:
        set_cookie_headers: List[bytes] = []
        normal_headers: Dict[str, str] = {}
        for k, v in raw_headers:
            if k.lower() == b"set-cookie":
                set_cookie_headers.append(v)
            elif k.lower() != b"content-length":
                normal_headers[k.decode()] = v.decode()
        return normal_headers, set_cookie_headers
