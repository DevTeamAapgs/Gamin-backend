from datetime import datetime
from typing import Optional, List
from pydantic import Field
from app.models.base import BaseDocument
from app.utils.pyobjectid import PyObjectId

class Player(BaseDocument):
    wallet_address: Optional[str] = Field(None, min_length=42, max_length=42)
    username: str = Field(...)
    email: Optional[str] = None
    token_balance: float = Field(default=0.0)
    total_games_played: int = Field(default=0)
    total_tokens_earned: float = Field(default=0.0)
    total_tokens_spent: float = Field(default=0.0)
    is_banned: bool = Field(default=False)
    ban_reason: Optional[str] = None
    device_fingerprint: Optional[str] = None
    ip_address: Optional[str] = None
    last_login: Optional[datetime] = None

class PlayerSession(BaseDocument):
    player_id: PyObjectId
    token_hash: str
    refresh_token: str
    device_fingerprint: str
    ip_address: str
    user_agent: Optional[str] = None
    expires_at: datetime
    last_activity: datetime = Field(default_factory=datetime.utcnow)

class PlayerTransaction(BaseDocument):
    player_id: PyObjectId
    transaction_type: str  # "game_entry", "reward", "withdrawal", "deposit"
    amount: float
    game_id: Optional[PyObjectId] = None
    description: str
    transaction_status: str = Field(default="pending")  # "pending", "completed", "failed"
    tx_hash: Optional[str] = None
    completed_at: Optional[datetime] = None 