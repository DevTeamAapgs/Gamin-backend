from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from pydantic import BaseModel, Field

from app.models.base import PyObjectId


class GameConfigurationSaveSchema(BaseModel):
    game_name: str = Field(..., description="The name of the game")
    game_type: str = Field(..., description="The type of the game")
    game_description: str = Field(..., description="The description of the game")
    game_banner: list[dict] = Field(default_factory=list, description="The description of the game")
    game_icon: dict = Field(default_factory=dict, description="The description of the game")

class GameConfigurationUpdateSchema(BaseModel):
    id: str = Field(..., description="The id of the game")
    game_name: str = Field(..., description="The name of the game")
    game_type: str = Field(..., description="The type of the game")
    game_description: str = Field(..., description="The description of the game")
    game_banner: list[dict] = Field(default_factory=list, description="The description of the game")
    game_icon: dict = Field(default_factory=dict, description="The description of the game")

class GameConfigurationGridResponse(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=ObjectId, alias="_id")
    game_name: str = Field(..., description="The name of the game")
    game_type: str = Field(..., description="The type of the game")
    game_description: str = Field(..., description="The description of the game")
    game_banner: list[dict] = Field(default_factory=list, description="The description of the game")
    game_icon: dict = Field(default_factory=dict, description="The description of the game")
    status: str = Field(..., description="The status of the game")

class GameConfigurationStatusUpdateSchema(BaseModel):
    id: str = Field(..., description="The id of the game")
    status: str = Field(..., description="The status of the game")


