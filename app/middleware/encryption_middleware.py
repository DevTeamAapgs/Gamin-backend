# app/response.py
from fastapi.responses import JSONResponse
from app.utils.crypto import encrypt_aes256

class EncryptedJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        encrypted_data = encrypt_aes256(str(content))
        return super().render({"data": encrypted_data})
