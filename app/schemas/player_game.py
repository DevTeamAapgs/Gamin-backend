from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class GameLevelItem(BaseModel):
    id: str
    level_name: str
    level_number: int
    description: str
    entry_cost: float
    reward_coins: float
    level_type: int
    entry_cost_gems: Dict[str, int]
    reward_gems: Dict[str, int]
    time_limit: int
    max_attempts: int
    add_details: List[Dict[str, Any]]
    status: int = 1
    created_at: datetime
    updated_at: Optional[datetime] = None

class GameListItem(BaseModel):
    id: str
    game_name: str
    game_type_name: int
    game_banner: List[Dict[str, Any]]
    game_icon: Dict[str, Any]
    game_assets: Optional[Dict[str, Any]] = None
    status: int = 1
    created_at: datetime
    updated_at: Optional[datetime] = None

class GameDetailItem(BaseModel):
    id: str
    game_name: str
    game_type_name: int
    game_banner: List[Dict[str, Any]]
    game_icon: Dict[str, Any]
    game_assets: Optional[Dict[str, Any]] = None
    status: int = 1
    created_at: datetime
    updated_at: Optional[datetime] = None
    levels: List[GameLevelItem] = []

class GameListResponse(BaseModel):
    games: List[GameListItem]
    total_count: int
    page: int
    page_size: int