from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from pydantic import BaseModel, Field

from app.core.enums import GameType
from app.models.base import PyObjectId


class GameConfigurationSaveSchema(BaseModel):
    game_name: str = Field(..., description="The name of the game")
    game_type: GameType = Field(..., description="The type of the game")
    game_description: str = Field(..., description="The description of the game")
    game_banner: list[dict] = Field(default_factory=list, description="The description of the game")
    game_icon: dict = Field(default_factory=dict, description="The description of the game")

class GameConfigurationUpdateSchema(BaseModel):
    id: str = Field(..., description="The id of the game")
    game_name: str = Field(..., description="The name of the game")
    game_type: GameType = Field(..., description="The type of the game")
    game_description: str = Field(..., description="The description of the game")
    game_banner: list[dict] = Field(default_factory=list, description="The description of the game")
    game_icon: dict = Field(default_factory=dict, description="The description of the game")


class GameConfigurationResponse(BaseModel):
    id: Optional[ObjectId] = Field(..., description="The id of the game")
    game_name: str = Field(..., description="The name of the game")
    game_type: GameType = Field(..., description="The type of the game")
    game_description: str = Field(..., description="The description of the game")
    game_banner: Optional[list[dict]] = Field(default_factory=list, description="The description of the game")
    game_icon: Optional[dict] = Field(default_factory=dict, description="The description of the game")
    status: int = Field(..., description="The status of the game")

    class Config:
        arbitrary_types_allowed = True
        populate_by_name = True  # Allows using both field name and alias for population
        json_encoders = {
            ObjectId: str
        }
        # Add this new configuration for Pydantic v2
        alias_generator = None  # Disable automatic alias generation
        allow_population_by_field_name = True  # Similar to populate_by_name


class GameConfigurationGridResponse(BaseModel):
    results: List[GameConfigurationResponse] = Field(default_factory=list, description="The results of the game configuration")
    pagination: int = Field(default=0, description="The pagination of the game configuration")

class GameConfigurationStatusUpdateSchema(BaseModel):
    id: str = Field(..., description="The id of the game")
    status: int = Field(..., description="The status of the game")



