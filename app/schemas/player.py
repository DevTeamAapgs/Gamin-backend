from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, EmailStr, Field
from app.core.enums import PlayerType

class RoleResponse(BaseModel):
    id: str = Field(..., alias="_id")
    role: str

class PlayerBase(BaseModel):
    username: str
    email: EmailStr
    status: int
    fk_role_id: str
    role: Optional[str] = None  # role name (joined)

class PlayerCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    status: int = 1

class PlayerUpdate(BaseModel):
    username: Optional[str]
    email: Optional[EmailStr]
    password: Optional[str]
    role: Optional[str]



class PlayerResponse(PlayerBase):
    id: str = Field(..., alias="_id")
    wallet_address: Optional[str]
    player_prefix: Optional[str]  # Add player prefix field
    # profile_photo dict fields:
    #   - uploadfilename: str
    #   - uploadurl: str
    #   - filesize_bytes: int (file size in bytes)
    #   - filesize_kb: float (file size in kilobytes, rounded to 2 decimals)
    profile_photo: Optional[Dict[str, str | int | float]] = None
    player_type: Optional[int] = Field(None, description="Player type: 0=SUPERADMIN, 1=ADMINEMPLOYEE, 2=PLAYER")
    is_verified: Optional[bool]
    token_balance: Optional[int]
    total_games_played: Optional[int]
    total_tokens_earned: Optional[int]
    created_at: Optional[datetime]
    last_login: Optional[datetime]

class PlayerFilters(BaseModel):
    status: Optional[int] = Field(None, description="Filter by status (1=active, 0=inactive)")
    role: Optional[str] = Field(None, description="Filter by role name")

class PlayerListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[PlayerResponse]

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