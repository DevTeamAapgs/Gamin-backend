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
from app.core.constants import GEM_COLORS
from typing import Union
import json


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

def safe_float_decrypt(value: Union[str, float, int], crypto: AESCipher) -> float:
    try:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # if the string looks like a number, just return it directly
            if value.strip().isdigit() or value.strip().replace(".", "", 1).isdigit():
                return float(value)
            decrypted = crypto.decrypt(value)
            return float(json.loads(decrypted))
    except Exception:
        return 0.0
    return 0.0


def decrypt_player_fields(data: dict) -> dict:
    crypto = AESCipher()
    try:
        data["token_balance"] = safe_float_decrypt(data.get("token_balance", "0"), crypto)
        data["total_tokens_earned"] = safe_float_decrypt(data.get("total_tokens_earned", "0"), crypto)
        data["total_tokens_spent"] = safe_float_decrypt(data.get("total_tokens_spent", "0"), crypto)
        # Decrypt each color in gems
        gems = data.get("gems", {"blue": "0", "green": "0", "red": "0"})
        decrypted_gems = {}
        for color in GEM_COLORS:
            enc_val = gems.get(color, "0")
            decrypted_gems[color] = int(safe_float_decrypt(enc_val, crypto))
        data["gems"] = GemType(**decrypted_gems)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decryption error: {str(e)}")
    return data
