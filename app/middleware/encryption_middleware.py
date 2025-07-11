import time
import logging
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.utils.crypto import AESCipher  # Your AES encryption utility

logger = logging.getLogger("middleware")
logger.setLevel(logging.INFO)

class ResponseEncryptionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, crypto: AESCipher):
        super().__init__(app)
        self.crypto = crypto

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Call downstream route
        response = await call_next(request)
        content_type = response.headers.get("content-type", "")

        # Read the full body into memory
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        # Bypass for Swagger/docs routes
        if (
            request.url.path in ["/openapi.json", "/docs", "/redoc"]
            or request.headers.get("x-plaintext", "").lower() == "true"
        ):
            return self._rebuild_response(body, response, content_type)

        # Only encrypt JSON responses
        if content_type.startswith("application/json"):
            try:
                original_text = body.decode("utf-8")
                encrypted = self.crypto.encrypt(original_text)

                elapsed = time.time() - start_time
                logger.info(
                    f"[EncryptMiddleware] {request.method} {request.url.path} | {len(original_text)} bytes | {elapsed:.4f}s"
                )

                encrypted_body = json.dumps({"data": encrypted}).encode("utf-8")
                return self._rebuild_response(encrypted_body, response, "application/json")
            except Exception as e:
                logger.exception("Encryption failed")
                return Response(
                    content=json.dumps({"error": f"Encryption failed: {str(e)}"}),
                    media_type="application/json",
                    status_code=500
                )

        # For non-JSON responses, return original body
        return self._rebuild_response(body, response, content_type)

    def _rebuild_response(self, body: bytes, original_response: Response, content_type: str) -> Response:
        """
        Creates a new Response preserving all headers including multiple Set-Cookie headers.
        """
        # Split Set-Cookie headers from others
        normal_headers, set_cookie_headers = self._split_set_cookie_headers(original_response.raw_headers)

        # Create new response with all original headers except cookies
        new_response = Response(
            content=body,
            status_code=original_response.status_code,
            headers=normal_headers,
            media_type=content_type
        )

        # Manually append each Set-Cookie header
        for set_cookie in set_cookie_headers:
            new_response.raw_headers.append((b'set-cookie', set_cookie))

        return new_response

    def _split_set_cookie_headers(self, raw_headers: list[tuple[bytes, bytes]]) -> tuple[dict[str, str], list[bytes]]:
        """
        Separates normal headers from all Set-Cookie headers.
        """
        set_cookie_headers = []
        normal_headers = {}

        for k, v in raw_headers:
            if k.lower() == b'set-cookie':
                set_cookie_headers.append(v)
            else:
                normal_headers[k.decode()] = v.decode()

        return normal_headers, set_cookie_headers
