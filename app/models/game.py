from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from bson import ObjectId
from pydantic import BaseModel, Field
from app.models.base import BaseDocument
from app.core.enums import GameStatus, GameActionType



class GemType(BaseModel):
  blue:int = Field(default=0)
  green:int = Field(default=0)
  red:int = Field(default=0)
  


class GameAttempt(BaseDocument):
    fk_player_id: ObjectId
    fk_game_configuration_id: ObjectId
    fk_game_level_id: ObjectId
    ip_address: Optional[str] = None
    device_fingerprint: Optional[str] = None
    level_number: int
    game_status: GameStatus = Field(default=GameStatus.ACTIVE)
    score: int = Field(default=0)
    tokens_earned: float = Field(default=0.0)
    gems_earned: GemType = Field(default=GemType(blue=0, green=0, red=0))
    entry_cost: float = Field(default=0.0)
    gems_spent: GemType = Field(default=GemType(blue=0, green=0, red=0))
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # in seconds
    moves_count: int = Field(default=0)
    max_moves: int = Field(default=100)
    game_data: Dict[str, Any] = Field(default_factory=dict)
    replay_data: List[Dict[str, Any]] = Field(default_factory=list)
    completion_percentage: float = Field(default=0.0)
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    game_type: Optional[str] = None

class GameAction(BaseDocument):
    fk_game_attempt_id: ObjectId
    fk_game_configuration_id: ObjectId
    fk_player_id: ObjectId
    action_type: GameActionType
    action_data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None

    
# class GameAttempt(BaseDocument):
#     fk_player_id: ObjectId
#     fk_game_configuration_id: ObjectId
#     attempt_number: int
#     start_time: datetime = Field(default_factory=datetime.utcnow)
#     end_time: Optional[datetime] = None
#     attempt_status: GameStatus = Field(default=GameStatus.ACTIVE)
#     score: int = Field(default=0)
#     tokens_earned: float = Field(default=0.0)
#     moves_count: int = Field(default=0)
#     completion_percentage: float = Field(default=0.0)

class GameAnalytics(BaseDocument):
    fk_player_id: ObjectId
    fk_game_configuration_id: ObjectId
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
    game_id: ObjectId
    fk_player_id: ObjectId
    replay_data: Dict[str, Any] = Field(default_factory=dict)
    action_sequence: List[Dict[str, Any]] = Field(default_factory=list)
    mouse_movements: List[Dict[str, Any]] = Field(default_factory=list)
    click_positions: List[Dict[str, Any]] = Field(default_factory=list)
    timing_data: Dict[str, Any] = Field(default_factory=dict)
    device_info: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None 