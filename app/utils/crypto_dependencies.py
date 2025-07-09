# app/dependencies.py
from fastapi import Request, Query, HTTPException, Depends
from app.utils.crypto import AESCipher


def get_crypto_service() -> AESCipher:
    return AESCipher()  # optionally pass a custom key


async def decrypt_body(request: Request, crypto: AESCipher = Depends(get_crypto_service)):
    try:
        body = await request.json()
        decrypted = {
            k: crypto.decrypt(v) if isinstance(v, str) else v
            for k, v in body.items()
        }
        return decrypted
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Decryption failed: {str(e)}")


def decrypt_query(query: str = Query(...), crypto: AESCipher = Depends(get_crypto_service)):
    try:
        return crypto.decrypt(query)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid encrypted query")
