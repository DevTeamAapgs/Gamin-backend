from datetime import datetime
from typing import Optional, List
from bson import objectid
from pydantic import Field, BaseModel
from app.models.base import BaseDocument, Status, DeletionStatus
from app.utils.pyobjectid import PyObjectId
from app.models.menu import MenuCard

class Player(BaseDocument):
    wallet_address: Optional[str] = Field(None, min_length=42, max_length=42)
    username: str = Field(...)
    email: Optional[str] = None
    token_balance: Optional[float] = Field(default=0.0)
    total_games_played: Optional[int] = Field(default=0)
    total_tokens_earned: Optional[float] = Field(default=0.0)
    total_tokens_spent: Optional[float] = Field(default=0.0)
    is_banned: bool = Field(default=False) 
    ban_reason: Optional[str] = None
    device_fingerprint: Optional[str] = None
    ip_address: Optional[str] = None
    last_login: Optional[datetime] = None
    player_type: int = Field(default=2)
    profile_photo: Optional[str] = None
    player_prefix: Optional[str] = None
    fk_role_id: Optional[PyObjectId] = Field(default=None)
class PlayerCreation(BaseDocument):
    wallet_address: Optional[str] = Field(None, min_length=42, max_length=42)
    username: str = Field(...)
    email: Optional[str] = None
    password_hash: str = Field(...)
    token_balance: Optional[float] = Field(default=0.0)
    total_games_played: Optional[int] = Field(default=0)
    total_tokens_earned: Optional[float] = Field(default=0.0)
    total_tokens_spent: Optional[float] = Field(default=0.0)
    is_banned: bool = Field(default=False) 
    ban_reason: Optional[str] = None
    device_fingerprint: Optional[str] = None
    ip_address: Optional[str] = None
    last_login: Optional[datetime] = None
    player_type: int = Field(default=2)
    profile_photo: Optional[str] = None
    player_prefix: Optional[str] = None
    fk_role_id: Optional[PyObjectId] = Field(default=None)

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



    
class PlayerResponse(BaseModel):
    id: str
    wallet_address: str
    username: str
    email: str
    token_balance: int
    total_games_played: int
    total_tokens_earned: int
    total_tokens_spent: int
    is_active: bool
    created_at: Optional[str]
    last_login: Optional[str]
    menus: List[MenuCard]
    
    
class PermissionItem(BaseModel):
    id: str
    menu_name: str
    menu_value: str
    menu_type: int
    menu_order: Optional[int]
    fk_parent_id: Optional[str]
    description: Optional[str]
    can_access: int
    router_url: Optional[str]

class MenuItem(BaseModel):
    id: str
    menu_name: str
    menu_value: str
    menu_type: int
    menu_order: Optional[int]
    fk_parent_id: Optional[str]
    can_show: Optional[int]
    router_url: Optional[str]
    menu_icon: Optional[str]
    active_urls: Optional[List[str]]
    mobile_access: Optional[int]
    permission: List[PermissionItem] = Field(default_factory=list)
    submenu: List['MenuItem'] = Field(default_factory=list)

    class Config:
        orm_mode = True

MenuItem.update_forward_refs()

class CustomPlayerResponse(BaseModel):
    page_count: int
    response_data: List[MenuItem]
    full_name: str
    profile_photo: Optional[str] 