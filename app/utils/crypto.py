import base64
import json
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Hash import SHA256


class AESCipher:
    def __init__(self, secret_key: str | None = None, mode: str = "CBC"):
        from app.core.config import settings
        self.secret_key = "your-super-secret-key-change-in-production"
        self.key =  SHA256.new(self.secret_key.encode('utf-8')).digest()
        self.mode = mode.upper()  # "CBC" or "CTR"

    @staticmethod
    def derive_key(secret: str) -> bytes:
        return SHA256.new(secret.encode('utf-8')).digest()

    def encrypt(self, data: str) -> str:
            data = json.dumps(data)
            iv = os.urandom(16)

            if self.mode == "CBC":
                cipher = AES.new(self.key, AES.MODE_CBC, iv)
                ct_bytes = cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))

            elif self.mode == "CTR":
                nonce = iv[:8]  # Use first 8 bytes as nonce
                cipher = AES.new(self.key, AES.MODE_CTR, nonce=nonce)
                ct_bytes = cipher.encrypt(data.encode('utf-8'))

            else:
                raise ValueError("Unsupported AES mode")

            encrypted = iv + ct_bytes  
            return base64.b64encode(encrypted).decode('utf-8')

    def decrypt(self, enc_data: str) -> str:
        try:
            raw = base64.urlsafe_b64decode(enc_data)
            iv, ct = raw[:16], raw[16:]

            if self.mode == "CBC":
                cipher = AES.new(self.key, AES.MODE_CBC, iv)
                decrypted = cipher.decrypt(ct)
                return unpad(decrypted, AES.block_size).decode('utf-8')

            elif self.mode == "CTR":
                cipher = AES.new(self.key, AES.MODE_CTR, nonce=iv[:8])
                decrypted = cipher.decrypt(ct)
                return decrypted.decode('utf-8')

            else:
                raise ValueError("Unsupported AES mode")

        except (ValueError, KeyError, TypeError, Exception) as e:
            raise ValueError(f"Decryption failed: {str(e)}")
