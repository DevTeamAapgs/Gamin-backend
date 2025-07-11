import json
from fastapi import Request, HTTPException, Depends, Query
from typing import Any, Type, TypeVar, Callable
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

def decrypt_body(model: Type[T]) -> Callable:
    print(model,"model")
    async def dependency(
        request: Request,
        crypto: AESCipher = Depends(get_crypto_service)
    ) -> T:
        try:
            body = await request.json()
            print(body,"body")
            # Skip encryption if requested (e.g. Swagger UI)
            if request.headers.get("x-plaintext", "").lower() == "true":
                return model(**body)

            decrypted:dict[str, Any] = {
                k: crypto.decrypt(v) if isinstance(v, str) else v
                for k, v in body.items()
            }
            print(decrypted,type(decrypted),"decrypeted")
            if 'data' in decrypted and decrypted['data']:
                decrypted = json.loads(decrypted['data'])

            return model(**decrypted)

        except Exception as e:
            print(e,"error")
            raise HTTPException(status_code=400, detail=f"Decryption failed: {str(e)}")
    
    return dependency


def decrypt_query(query: str = Query(...), crypto: AESCipher = Depends(get_crypto_service)):
    try:
        return crypto.decrypt(query)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid encrypted query")


def decrypt_data_param(
    data: str = Query(...),
    request: Request = Depends(),
    crypto: AESCipher = Depends(get_crypto_service)
) -> dict:
    if request and request.headers.get("x-plaintext", "").lower() == "true":
        return eval(data) if isinstance(data, str) else data
    try:
        decrypted_json = crypto.decrypt(data)
        return eval(decrypted_json)  
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to decrypt query payload")