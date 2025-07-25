from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field
from app.core.enums import PlayerType
from app.models.base import BaseDocument, PyObjectId
from app.models.game import GemType
class RoleResponse(BaseModel):
    id: str = Field(..., alias="_id")
    role: str

class PlayerBase(BaseModel):
    username: str
    email: EmailStr
    status: int
    fk_role_id: str

class PlayerCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    status: int = 1
    otp: Optional[str] = None

class PlayerUpdate(BaseModel):
    username: Optional[str]
    email: Optional[EmailStr]
    password: Optional[str]
    role: Optional[str]


class PlayerInfoSchema(BaseDocument):
    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")
    wallet_address: Optional[str] = Field(None, min_length=42, max_length=42)
    username: str = Field(...)
    email: Optional[str] = None
    token_balance: Optional[float] = Field(default=0.0)
    total_games_played: Optional[int] = Field(default=0)
    total_tokens_earned: Optional[float] = Field(default=0.0)
    total_tokens_spent: Optional[float] = Field(default=0.0)
    gems: Optional[GemType] = Field(default=GemType(blue=0, green=0, red=0))
    is_banned: bool = Field(default=False) 
    ban_reason: Optional[str] = None
    device_fingerprint: Optional[str] = None
    ip_address: Optional[str] = None
    last_login: Optional[datetime] = None
    player_type: int = Field(default=2)
    profile_photo: Optional[str] = None
    player_prefix: Optional[str] = None
    fk_role_id: Optional[PyObjectId] = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = None


class PlayerResponse(BaseModel):
    id: str 
    wallet_address: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    token_balance: Optional[int] = None
    total_games_played: Optional[int] = None
    total_tokens_earned: Optional[int] = None
    total_tokens_spent: Optional[int] = None
    gems: Optional[GemType] = None
    is_active: Optional[bool] = None
    created_at: Optional[str] = None
    last_login: Optional[datetime] = None
    menus: Optional[List] = Field(default_factory=list)
    player_prefix: Optional[str] = None
    profile_photo: Optional[Dict[str, str | int | float]] = None
    player_type: Optional[int] = Field(None, description="Player type: 0=SUPERADMIN, 1=ADMINEMPLOYEE, 2=PLAYER")
    is_verified: Optional[bool] = None

class PlayerFilters(BaseModel):
    status: Optional[int] = Field(None, description="Filter by status (1=active, 0=inactive)")
    role: Optional[str] = Field(None, description="Filter by role name")

class PlayerListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[PlayerResponse]

class PlayerLogin(BaseModel):
    email: Optional[str] = Field(None, min_length=42, max_length=42)
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


class PlayerAdminGridListItem(BaseModel):
    id: str
    username: str
    email: Optional[str]
    wallet_status: bool = False
    ip_address: Optional[str] = None
    token_balance: float = 0.0
    is_banned: bool = False
    status: int 

class PlayerAdminGridListResponse(BaseModel):
    results: list[PlayerAdminGridListItem]
    pagination: int 



class PlayerAdminResponseWithId(BaseModel):
    id: str 
    wallet_address: Optional[str] = None
    player_prefix: Optional[str] = None    # Add player prefix field
    is_banned: Optional[str] = None
    created_on: datetime 
    # profile_photo dict fields:
    #   - uploadfilename: str
    #   - uploadurl: str
    #   - filesize_bytes: int (file size in bytes)
    #   - filesize_kb: float (file size in kilobytes, rounded to 2 decimals)
    profile_photo: Optional[Dict[str, str | int | float]] = None
    player_type: Optional[int] = Field(None, description="Player type: 0=SUPERADMIN, 1=ADMINEMPLOYEE, 2=PLAYER")
    is_verified: Optional[bool] = None
    token_balance: Optional[int]
    total_games_played: Optional[int]
    total_tokens_earned: Optional[int]
    username: Optional[str]
    email: Optional[EmailStr]
    last_login: Optional[datetime]