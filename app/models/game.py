from datetime import datetime
from typing import Optional, List, Dict, Any, Annotated
from pydantic import BaseModel, Field, BeforeValidator
from bson import ObjectId
from app.models.player import PyObjectId

class Game(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=ObjectId, alias="_id")
    player_id: PyObjectId
    game_type: str = Field(default="color_match")  # "color_match", "tube_filling"
    level_number: int
    status: str = Field(default="active")  # "active", "completed", "failed", "abandoned"
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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

class GameLevel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=ObjectId, alias="_id")
    level_number: int
    game_type: str = Field(default="color_match")
    name: str
    description: str
    entry_cost: float
    reward_multiplier: float = Field(default=1.0)
    time_limit: int  # in seconds
    difficulty_multiplier: float = Field(default=1.0)
    max_attempts: int = Field(default=3)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

class GameAction(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=ObjectId, alias="_id")
    game_id: PyObjectId
    player_id: PyObjectId
    action_type: str  # "move", "click", "drag", "drop", "complete", "fail"
    action_data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

class GameAttempt(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=ObjectId, alias="_id")
    player_id: PyObjectId
    level_number: int
    game_type: str
    attempt_number: int
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: str = Field(default="in_progress")  # "in_progress", "completed", "failed"
    score: int = Field(default=0)
    tokens_earned: float = Field(default=0.0)
    moves_count: int = Field(default=0)
    completion_percentage: float = Field(default=0.0)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

class GameAnalytics(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=ObjectId, alias="_id")
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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

class GameReplay(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=ObjectId, alias="_id")
    game_id: PyObjectId
    player_id: PyObjectId
    replay_data: Dict[str, Any] = Field(default_factory=dict)
    action_sequence: List[Dict[str, Any]] = Field(default_factory=list)
    mouse_movements: List[Dict[str, Any]] = Field(default_factory=list)
    click_positions: List[Dict[str, Any]] = Field(default_factory=list)
    timing_data: Dict[str, Any] = Field(default_factory=dict)
    device_info: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    } 