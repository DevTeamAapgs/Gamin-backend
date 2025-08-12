from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class GameStart(BaseModel):
    game_type: str = Field(default="color_match")
    level: int = Field(..., ge=1, le=10)
    device_fingerprint: str

class GameSubmit(BaseModel):
    game_id: str
    completion_percentage: float = Field(..., ge=0, le=100)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    mouse_movements: List[Dict[str, Any]] = Field(default_factory=list)
    click_positions: List[Dict[str, Any]] = Field(default_factory=list)
    timing_data: Dict[str, Any] = Field(default_factory=dict)
    device_info: Dict[str, Any] = Field(default_factory=dict)

class GameResponse(BaseModel):
    id: str
    player_id: str
    game_type: str
    level: int
    status: str
    entry_cost: float
    reward_multiplier: float
    time_limit: int
    completion_percentage: float
    final_reward: Optional[float] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    created_at: datetime

class GameLevelResponse(BaseModel):
    id: str
    level_number: int
    game_type: str
    name: str
    description: str
    entry_cost: float
    reward_multiplier: float
    time_limit: int
    difficulty_multiplier: float
    max_attempts: int
    is_active: bool

class GameLevelUpdate(BaseModel):
    entry_cost: Optional[float] = Field(None, gt=0)
    reward_multiplier: Optional[float] = Field(None, gt=0)
    time_limit: Optional[int] = Field(None, gt=0)
    difficulty_multiplier: Optional[float] = Field(None, gt=0)
    max_attempts: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None

class GameAnalyticsResponse(BaseModel):
    id: str
    game_id: str
    player_id: str
    heatmap_data: Dict[str, Any]
    click_frequency: Dict[str, int]
    time_spent_per_section: Dict[str, float]
    rage_quit_zones: List[Dict[str, Any]]
    retry_patterns: Dict[str, Any]
    completion_patterns: Dict[str, Any]
    created_at: datetime

class ReplayResponse(BaseModel):
    id: str
    game_id: str
    player_id: str
    action_sequence: List[Dict[str, Any]]
    mouse_movements: List[Dict[str, Any]]
    click_positions: List[Dict[str, Any]]
    timing_data: Dict[str, Any]
    device_info: Dict[str, Any]
    created_at: datetime

class LeaderboardEntry(BaseModel):
    player_id: str
    username: str
    wallet_address: Optional[str] 
    total_tokens_earned: float
    total_games_played: int
    win_rate: float
    average_completion: float
    rank: int

class LeaderboardResponse(BaseModel):
    entries: List[LeaderboardEntry]
    total_players: int
    page: int
    page_size: int 
    
class JoinGameRequest(BaseModel):
    player_id: str
    game_level_id: str
    game_type: str
    device_fingerprint: Optional[str] = None
    ip_address: Optional[str] = None
    level_type: int

class JoinGameResponse(BaseModel):
    game_attempt_id: str
    message: str

class ExitGameRequest(BaseModel):
    player_id: str
    score: float
    completion_percentage: Optional[float] = 0.0
    replay_data: Optional[List[Dict[str, Any]]] = []

class ExitGameResponse(BaseModel):
    message: str
    tokens_earned: float
    gems_earned: Dict[str, int]

class GameActionRequest(BaseModel):
    player_id: str
    action_type: str
    action_data: Optional[Dict[str, Any]] = {}
    session_id: Optional[str] = None
    timestamp: Optional[str] = None

class GameActionResponse(BaseModel):
    game_attempt_id: str
    action_id: str
    action_type: str
    timestamp: Optional[str] = None

class GameStateUpdateRequest(BaseModel):
    player_id: str
    timestamp: Optional[str] = None

class GameStateUpdateResponse(BaseModel):
    game_attempt_id: str
    timestamp: Optional[str] = None

class ChatMessageRequest(BaseModel):
    player_id: str
    username: str
    message: str
    timestamp: Optional[str] = None

class PingRequest(BaseModel):
    timestamp: Optional[str] = None

class PingResponse(BaseModel):
    timestamp: Optional[str] = None
