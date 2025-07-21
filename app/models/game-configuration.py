from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.core.enums import GameType
from app.models.base import BaseDocument
from app.utils.pyobjectid import PyObjectId

class GameConfigurationModel(BaseDocument):
    game_name: str = Field(..., description="The name of the game")
    game_description: str = Field(..., description="The description of the game")
    game_banner: list[dict] = Field(default_factory=list, description="The description of the game")
    game_icon: dict = Field(default_factory=dict, description="The description of the game")
    game_type: GameType = Field(default=GameType.MainGame)  
    

class AddDetails(BaseModel):
    time_mintues: int
    number_of_adds: int

class GameLevelConfigurationModel(BaseDocument):
    level_name: str
    level_number: int
    description: str
    fk_game_id:PyObjectId 
    entry_cost: float
    reward_coins: float = Field(default=1)
    time_limit: int 
    max_attempts: int = Field(default=3)
    add_details: list[AddDetails] = Field(default_factory=list, description="The description of the game")
