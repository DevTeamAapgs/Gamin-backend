from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from bson import ObjectId
from pydantic import BaseModel, Field
from app.models.base import BaseDocument
from app.models.game import GemType


class PlayerBannedDetails(BaseDocument):
    fk_player_id: ObjectId
    reason: str
    banned_status: bool = Field(default=True)
    banned_until: Optional[datetime] = None
    banned_by_name: Optional[str] = None
    banned_by_ip: Optional[str] = None
    banned_by_device_fingerprint: Optional[str] = None
    