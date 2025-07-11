from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class PlayerCreate(BaseModel):
    wallet_address: Optional[str] = Field(None, min_length=42, max_length=42)
    username: str = Field(..., min_length=3, max_length=20)
    email: Optional[EmailStr] = None
    device_fingerprint: Optional[str] = None

class PlayerLogin(BaseModel):
    wallet_address: Optional[str] = Field(None, min_length=42, max_length=42)
    device_fingerprint: str
    ip_address: str

class AdminLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)

class AdminCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6, max_length=100)
    email: Optional[EmailStr] = None

class PlayerUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=20)
    email: Optional[EmailStr] = None

class PlayerResponse(BaseModel):
    id: str
    wallet_address: Optional[str] 
    username: str
    email: Optional[str] = None
    token_balance: float
    total_games_played: int
    total_tokens_earned: float
    total_tokens_spent: float
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class AdminResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    is_admin: bool
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class PlayerBalance(BaseModel):
    token_balance: float
    total_earned: float
    total_spent: float

class PlayerStats(BaseModel):
    total_games_played: int
    games_won: int
    games_lost: int
    win_rate: float
    average_completion: float
    total_tokens_earned: float
    total_tokens_spent: float
    net_profit: float

class TransactionCreate(BaseModel):
    amount: float = Field(..., gt=0)
    transaction_type: str = Field(..., pattern="^(game_entry|reward|withdrawal|deposit)$")
    game_id: Optional[str] = None
    description: str

class TransactionResponse(BaseModel):
    id: str
    player_id: str
    transaction_type: str
    amount: float
    game_id: Optional[str] = None
    description: str
    status: str
    tx_hash: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class BanRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for banning the player") 