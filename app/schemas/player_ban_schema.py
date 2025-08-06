from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class BanPlayerRequest(BaseModel):
    player_id: str = Field(..., description="Player's ObjectId as string")
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for banning the player")

class UnbanPlayerRequest(BaseModel):
    fk_player_id: str = Field(..., description="Player's ObjectId as string")
    banned_until: Optional[datetime] = Field(default_factory=datetime.now, description="Datetime until which the player is banned (optional)") 