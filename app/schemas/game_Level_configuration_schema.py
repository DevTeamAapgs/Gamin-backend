from typing import Optional, List
from bson import ObjectId
from pydantic import BaseModel, Field
from app.utils.pyobjectid import PyObjectId

class AddDetailsSchema(BaseModel):
    time_mintues: int
    number_of_adds: int

class GameLevelConfigurationSaveSchema(BaseModel):
    level_name: str
    level_number: int
    description: str
    fk_game_configuration_id: str
    entry_cost: float
    reward_coins: float = Field(default=1)
    time_limit: int
    max_attempts: int = Field(default=3)
    add_details: List[AddDetailsSchema] = Field(default_factory=list)

class GameLevelConfigurationUpdateSchema(BaseModel):
    id: str
    level_name: str
    level_number: int
    description: str
    fk_game_configuration_id: str
    entry_cost: float
    reward_coins: float = Field(default=1)
    time_limit: int
    max_attempts: int = Field(default=3)
    add_details: List[AddDetailsSchema] = Field(default_factory=list)

class GameLevelConfigurationResponse(BaseModel):
    id: Optional[PyObjectId] 
    level_name: str
    level_number: int
    description: str
    fk_game_configuration_id: PyObjectId
    entry_cost: float
    reward_coins: float
    time_limit: int
    max_attempts: int
    add_details: List[AddDetailsSchema] = Field(default_factory=list)
    status: Optional[int] = 1

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}

class GameLevelConfigurationGridResponse(BaseModel):
    results: List[GameLevelConfigurationResponse] = Field(default_factory=list)
    total: int = Field(default=0)

class GameLevelConfigurationStatusUpdateSchema(BaseModel):
    id: str
    status: int
