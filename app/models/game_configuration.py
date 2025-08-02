from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from pydantic import BaseModel, Field
from app.core.enums import GameType, GameTypeName
from app.models.base import BaseDocument
from app.utils.pyobjectid import PyObjectId
from app.models.game import GemType
class GameConfigurationModel(BaseDocument):
    game_name: str = Field(..., description="The name of the game")
    game_description: str = Field(..., description="The description of the game")
    game_type_name: GameTypeName = Field(..., description="The type name of the game")
    game_banner: list[dict] = Field(default_factory=list, description="The description of the game")
    game_icon: dict = Field(default_factory=dict, description="The description of the game")
    game_assets: Optional[dict] = Field(default=None, description="The game assets directory info")
    

class AddDetails(BaseModel):
    time_mintues: int
    number_of_adds: int

class GameLevelConfigurationModel(BaseDocument):
    level_name: str
    level_number: int
    description: str
    fk_game_configuration_id:ObjectId 
    entry_cost: float
    reward_coins: float = Field(default=1)
    
    level_type: LevelType   
    entry_cost_gems: GemType = Field(default=GemType(blue=0, green=0, red=0))
    reward_gems: GemType = Field(default=GemType(blue=0, green=0, red=0))
    
    time_limit: int

    max_attempts: int = Field(default=3)
    add_details: list[AddDetails] = Field(default_factory=list, description="The description of the game")
