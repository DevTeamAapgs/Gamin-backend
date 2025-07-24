import base64
import json
import os
from Crypto.Cipher import AES
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Hash import SHA256 
from app.utils.crypto import AESCipher
from fastapi import HTTPException
from app.models.game import GemType

ENCRYPTED_FIELDS = [
    "token_balance", "total_tokens_earned", "total_tokens_spent",
    "gems.blue", "gems.red", "gems.green"
]

def encrypt_player_fields(player_dict: dict, crypto: AESCipher) -> dict:
    for field in ENCRYPTED_FIELDS:
        keys = field.split(".")
        if len(keys) == 1:
            key = keys[0]
            if key in player_dict and player_dict[key] is not None:
                player_dict[key] = crypto.encrypt(str(player_dict[key]))
        elif len(keys) == 2:
            outer, inner = keys
            if outer in player_dict and isinstance(player_dict[outer], dict):
                if inner in player_dict[outer] and player_dict[outer][inner] is not None:
                    player_dict[outer][inner] = crypto.encrypt(str(player_dict[outer][inner]))
    return player_dict

def decrypt_player_fields(data: dict) -> dict:
    crypto = AESCipher()
    try:
        data["token_balance"] = float(crypto.decrypt(data.get("token_balance", "0")))
        data["total_tokens_earned"] = float(crypto.decrypt(data.get("total_tokens_earned", "0")))
        data["total_tokens_spent"] = float(crypto.decrypt(data.get("total_tokens_spent", "0")))
        data["gems"] = GemType(**json.loads(crypto.decrypt(data.get("gems", "{}"))))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decryption error: {str(e)}")
    return data
