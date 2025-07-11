import json
from fastapi import Request, HTTPException, Depends, Query
from typing import Any, Type, TypeVar, Callable

from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.utils.crypto import AESCipher

T = TypeVar("T")

def get_crypto_service() -> AESCipher:
    return AESCipher()

# def decrypt_body(model: Type[T]) -> Callable:
#     async def dependency(
#         request: Request,
#         crypto: AESCipher = Depends(get_crypto_service)
#     ) -> T:
#         try:
#             body = await request.json()
#             print(body,"body")
#             # Skip encryption if requested (e.g. Swagger UI)
#             if request.headers.get("x-plaintext", "").lower() == "true":
#                 return model(**body)

#             decrypted = {
#                 k: crypto.decrypt(v) if isinstance(v, str) else v
#                 for k, v in body.items()
#             }
#             print(decrypted,"decrypted")
#             return model(**decrypted)

#         except Exception as e:
#             raise HTTPException(status_code=400, detail=f"Decryption failed: {str(e)}")
    
#     return dependency


def decrypt_body(model: Type[T]) -> Callable[..., T]:
    async def dependency(
        request: Request,
        crypto: AESCipher = Depends(get_crypto_service)
    ) -> T:
        try:
            body = await request.json()
            if request.headers.get("x-plaintext", "").lower() == "true":
                return model(**body)

            decrypted: dict[str, Any] = {
                k: crypto.decrypt(v) if isinstance(v, str) else v
                for k, v in body.items()
            }

            # If decrypted contains a nested 'data' stringified JSON
            if isinstance(decrypted.get("data"), str):
                decrypted = json.loads(decrypted["data"])

            return model(**decrypted)

        except Exception as e:
            print("Decryption failed:", e)
            raise HTTPException(status_code=400, detail=f"Decryption failed: {str(e)}")

    return dependency

def decrypt_query(query: str = Query(...), crypto: AESCipher = Depends(get_crypto_service)):
    try:
        return crypto.decrypt(query)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid encrypted query")


def decrypt_data_param(
    data: str = Query(...),
    request: Request = None,
    crypto: AESCipher = Depends(get_crypto_service)
) -> dict:
    if request and request.headers.get("x-plaintext", "").lower() == "true":
        return eval(data) if isinstance(data, str) else data
    try:
        decrypted_json = crypto.decrypt(data)
        return eval(decrypted_json)  
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to decrypt query payload")



def get_encryptor_response(crypto: AESCipher = Depends(get_crypto_service)) -> Callable:
    def encrypt_response(data: Any, request: Request | None = None) -> JSONResponse:
        """Encrypt response data and return JSONResponse"""
        try:
            # Skip encryption if x-plaintext header is set to "true" (for Swagger UI)
            if request and request.headers.get("x-plaintext", "").lower() == "true":
                return data
            
            # Handle different data types for encryption
            if hasattr(data, 'model_dump'):
                # Pydantic model
                json_str = json.dumps(data.model_dump(), default=str)
            elif isinstance(data, dict):
                # Dictionary
                json_str = json.dumps(data, default=str)
            elif isinstance(data, (list, tuple)):
                # List or tuple
                json_str = json.dumps(data, default=str)
            else:
                # Other types - convert to string
                json_str = json.dumps(data, default=str)
            
            encrypted = crypto.encrypt(json_str)
            return JSONResponse(content={"data": encrypted})
        except Exception as e:
            # Fallback to plain response if encryption fails
            return JSONResponse(content=data)
    
    return encrypt_response       