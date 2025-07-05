from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field
from app.models.base import BaseDocument, PyObjectId

class Game(BaseDocument):
    player_id: PyObjectId
    game_type: str = Field(default="color_match")  # "color_match", "tube_filling"
    level_number: int
    game_status: str = Field(default="active")  # "active", "completed", "failed", "abandoned"
    score: int = Field(default=0)
    tokens_earned: float = Field(default=0.0)
    entry_cost: float = Field(default=0.0)
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # in seconds
    moves_count: int = Field(default=0)
    max_moves: int = Field(default=100)
    game_data: Dict[str, Any] = Field(default_factory=dict)
    replay_data: List[Dict[str, Any]] = Field(default_factory=list)

class GameLevel(BaseDocument):
    level_number: int
    game_type: str = Field(default="color_match")
    name: str
    description: str
    entry_cost: float
    reward_multiplier: float = Field(default=1.0)
    time_limit: int  # in seconds
    difficulty_multiplier: float = Field(default=1.0)
    max_attempts: int = Field(default=3)

class GameAction(BaseDocument):
    game_id: PyObjectId
    player_id: PyObjectId
    action_type: str  # "move", "click", "drag", "drop", "complete", "fail"
    action_data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None

class GameAttempt(BaseDocument):
    player_id: PyObjectId
    level_number: int
    game_type: str
    attempt_number: int
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    attempt_status: str = Field(default="in_progress")  # "in_progress", "completed", "failed"
    score: int = Field(default=0)
    tokens_earned: float = Field(default=0.0)
    moves_count: int = Field(default=0)
    completion_percentage: float = Field(default=0.0)

class GameAnalytics(BaseDocument):
    player_id: PyObjectId
    game_type: str
    level_number: int
    total_attempts: int = Field(default=0)
    successful_attempts: int = Field(default=0)
    total_tokens_earned: float = Field(default=0.0)
    average_completion_time: float = Field(default=0.0)
    best_completion_time: Optional[float] = None
    average_score: float = Field(default=0.0)
    best_score: int = Field(default=0)
    last_played: Optional[datetime] = None

class GameReplay(BaseDocument):
    game_id: PyObjectId
    player_id: PyObjectId
    replay_data: Dict[str, Any] = Field(default_factory=dict)
    action_sequence: List[Dict[str, Any]] = Field(default_factory=list)
    mouse_movements: List[Dict[str, Any]] = Field(default_factory=list)
    click_positions: List[Dict[str, Any]] = Field(default_factory=list)
    timing_data: Dict[str, Any] = Field(default_factory=dict)
    device_info: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None 