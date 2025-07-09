import base64
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from hashlib import sha256

from app.core.config import settings


class AESCipher:
    def __init__(self, secret_key: str|None = None):
        self.secret_key = os.getenv("AES_SECRET_KEY", settings.aes_key)
        self.key = self.derive_key(self.secret_key)

    @staticmethod
    def derive_key(secret: str) -> bytes:
        """Derives a 256-bit key using SHA-256."""
        return sha256(secret.encode()).digest()

    def encrypt(self, data: str) -> str:
        """Encrypts the input string using AES-256-CBC and returns base64-safe string."""
        iv = os.urandom(16)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        ct_bytes = cipher.encrypt(pad(data.encode(), AES.block_size))
        return base64.urlsafe_b64encode(iv + ct_bytes).decode()

    def decrypt(self, enc_data: str) -> str:
        """Decrypts a base64-safe AES-256-CBC encrypted string."""
        raw = base64.urlsafe_b64decode(enc_data)
        iv, ct = raw[:16], raw[16:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(ct), AES.block_size).decode()
