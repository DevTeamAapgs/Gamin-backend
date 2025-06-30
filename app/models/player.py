from datetime import datetime
from typing import Optional, List, Any, Annotated
from pydantic import BaseModel, Field, BeforeValidator
from bson import ObjectId

def validate_object_id(v: Any) -> ObjectId:
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str):
        if ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId string")
    raise ValueError("Invalid ObjectId")

PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]

class Player(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=ObjectId, alias="_id")
    wallet_address: str = Field(...)
    username: str = Field(...)
    email: Optional[str] = None
    token_balance: float = Field(default=0.0)
    total_games_played: int = Field(default=0)
    total_tokens_earned: float = Field(default=0.0)
    total_tokens_spent: float = Field(default=0.0)
    is_active: bool = Field(default=True)
    is_banned: bool = Field(default=False)
    ban_reason: Optional[str] = None
    device_fingerprint: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

class PlayerSession(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=ObjectId, alias="_id")
    player_id: PyObjectId
    token_hash: str
    refresh_token: str
    device_fingerprint: str
    ip_address: str
    user_agent: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    last_activity: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

class PlayerTransaction(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=ObjectId, alias="_id")
    player_id: PyObjectId
    transaction_type: str  # "game_entry", "reward", "withdrawal", "deposit"
    amount: float
    game_id: Optional[PyObjectId] = None
    description: str
    status: str = Field(default="pending")  # "pending", "completed", "failed"
    tx_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    } 