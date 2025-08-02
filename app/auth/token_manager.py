from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends
from jose import JWTError, jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import hashlib
import json
import logging
from bson import ObjectId

from app.core.config import settings
from app.models.player import Player, PlayerSession
from app.db.mongo import get_database

logger = logging.getLogger(__name__)

class TokenManager:
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.refresh_token_expire_days = settings.refresh_token_expire_days

        # Static AES encryption key (for encrypting seed and outer layer)
        self.aes_key = self._derive_aes_key(settings.aes_key)
        self.cipher_suite = Fernet(self.aes_key)

    def _derive_aes_key(self, key: str) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=settings.salt.encode(),
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(key.encode()))

    def _generate_token_seed(self) -> str:
        current_hour = datetime.utcnow().strftime("%Y%m%d%H")
        return hashlib.sha256(f"{current_hour}{self.secret_key}".encode()).hexdigest()

    def _create_layered_token(self, data: Dict[str, Any], token_type: str = "access") -> str:
        seed = self._generate_token_seed()

        # JWT payload
        to_encode = data.copy()
        expire = datetime.utcnow() + (
            timedelta(minutes=self.access_token_expire_minutes) if token_type == "access"
            else timedelta(days=self.refresh_token_expire_days)
        )
        to_encode.update({
            "exp": expire,
            "type": token_type,
            "seed": seed
        })
        jwt_token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        # Encrypt JWT with seed-derived key
        seed_key = self._derive_aes_key(seed)
        cipher_jwt = Fernet(seed_key)
        encrypted_jwt = cipher_jwt.encrypt(jwt_token.encode()).decode()

        # Encrypt seed with static key
        encrypted_seed = self.cipher_suite.encrypt(seed.encode()).decode()

        # Outer payload
        payload = json.dumps({"token": encrypted_jwt, "seed": encrypted_seed})
        final_token = self.cipher_suite.encrypt(payload.encode()).decode()

        return final_token

    def create_access_token(self, data: Dict[str, Any]) -> str:
        return self._create_layered_token(data, "access")

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        return self._create_layered_token(data, "refresh")

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify access token."""
        return self.verify_layered_token(token, "access")

    def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify refresh token."""
        return self.verify_layered_token(token, "refresh")

    def verify_layered_token(self, layered_token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        try:
            decrypted_outer = self.cipher_suite.decrypt(layered_token.encode()).decode()
            payload = json.loads(decrypted_outer)

            decrypted_seed = self.cipher_suite.decrypt(payload["seed"].encode()).decode()
            seed_key = self._derive_aes_key(decrypted_seed)
            cipher_jwt = Fernet(seed_key)
            jwt_token = cipher_jwt.decrypt(payload["token"].encode()).decode()

            decoded = jwt.decode(jwt_token, self.secret_key, algorithms=[self.algorithm])

            if decoded.get("type") != token_type:
                raise JWTError("Invalid token type")
            if decoded.get("seed") != decrypted_seed:
                raise JWTError("Seed mismatch")

            return decoded
        except Exception as e:
            logger.error(f"Layered token verification failed: {e}")
            return None

    async def create_player_session(self, player, device_fingerprint: str, ip_address: str, user_agent: str) -> PlayerSession:
        db = get_database()

        # Ensure player has an ID
        if player.get("id") is None:
            raise Exception("Player ID cannot be None")

        access_token = self.create_access_token({"sub": str(player.get("id")), "wallet": player.get("wallet_address")   })
        refresh_token = self.create_refresh_token({"sub": str(player.get("id")), "wallet": player.get("wallet_address")})

        session = PlayerSession(**{
            "player_id": player.get("id"),  
            "token_hash": hashlib.sha256(access_token.encode()).hexdigest(),
            "refresh_token": refresh_token,
            "device_fingerprint": device_fingerprint,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "expires_at": datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        })
        await db.sessions.insert_one(session.model_dump())
        return session

    async def validate_session(self, token_hash: str, device_fingerprint: str, ip_address: str) -> Optional[PlayerSession]:
        db = Depends(get_database)

        session = await db.sessions.find_one({
            "token_hash": token_hash,
            "device_fingerprint": device_fingerprint,
            "ip_address": ip_address,
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow()}
        })

        if session:
            return PlayerSession(**session)
        return None

    async def invalidate_session(self, token_hash: str) -> bool:
        db = Depends(get_database)

        result = await db.sessions.update_one(
            {"token_hash": token_hash},
            {"$set": {"status": 0}}
        )

        return result.modified_count > 0

    async def cleanup_expired_sessions(self) -> int:
        db = Depends(get_database)

        result = await db.sessions.update_many(
            {"expires_at": {"$lt": datetime.utcnow()}},
            {"$set": {"status": 0}}
        )

        return result.modified_count

token_manager = TokenManager()
