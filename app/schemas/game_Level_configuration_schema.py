from typing import Optional, List
from bson import ObjectId
from pydantic import BaseModel, Field
from app.core.enums import LevelType
from app.utils.pyobjectid import PyObjectId
from app.models.game import GemType

class AddDetailsSchema(BaseModel):
    time_mintues: int
    number_of_adds: int

class GameLevelConfigurationSaveSchema(BaseModel):
    level_name: str
    level_number: int
    level_type: LevelType
    description: str
    fk_game_configuration_id: str
    entry_cost: float
    entry_cost_gems: GemType = Field(default=GemType(blue=0, green=0, red=0))
    reward_coins: float = Field(default=1)
    reward_gems: GemType = Field(default=GemType(blue=0, green=0, red=0))
    time_limit: int
    max_attempts: int = Field(default=3)
    add_details: List[AddDetailsSchema] = Field(default_factory=list)

class GameLevelConfigurationUpdateSchema(BaseModel):
    id: str
    level_name: str
    level_number: int
    level_type: LevelType
    description: str
    fk_game_configuration_id: str
    entry_cost: float
    entry_cost_gems: GemType = Field(default=GemType(blue=0, green=0, red=0))
    reward_coins: float = Field(default=1)
    reward_gems: GemType = Field(default=GemType(blue=0, green=0, red=0))
    time_limit: int
    max_attempts: int = Field(default=3)
    add_details: List[AddDetailsSchema] = Field(default_factory=list)

class GameLevelConfigurationResponse(BaseModel):
    id: Optional[PyObjectId] 
    level_name: str
    level_number: int
    level_type: LevelType
    description: str
    fk_game_configuration_id: PyObjectId
    entry_cost: float = Field(default=0)
    entry_cost_gems: GemType = Field(default=GemType(blue=0, green=0, red=0))
    reward_coins: float = Field(default=0)
    reward_gems: GemType = Field(default=GemType(blue=0, green=0, red=0))
    time_limit: int
    max_attempts: int
    add_details: List[AddDetailsSchema] = Field(default_factory=list)
    status: Optional[int] = 1

    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}

class GameLevelConfigurationGridResponse(BaseModel):
    results: List[GameLevelConfigurationResponse] = Field(default_factory=list)
    total: int = Field(default=0)

class GameLevelConfigurationStatusUpdateSchema(BaseModel):
    id: str
    status: int
