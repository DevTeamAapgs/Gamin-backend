from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId
from app.models.player import PyObjectId

class RequestLog(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=ObjectId, alias="_id")
    method: str
    path: str
    status_code: int
    client_ip: str
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None
    player_id: Optional[PyObjectId] = None
    request_headers: Dict[str, str] = Field(default_factory=dict)
    response_headers: Dict[str, str] = Field(default_factory=dict)
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    process_time: float  # in seconds
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ttl: Optional[datetime] = None  # For automatic cleanup

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

class SecurityLog(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=ObjectId, alias="_id")
    event_type: str  # "failed_login", "suspicious_activity", "ban", "cheat_detected"
    player_id: Optional[PyObjectId] = None
    client_ip: str
    device_fingerprint: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    severity: str = Field(default="info")  # "info", "warning", "error", "critical"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ttl: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

class GameActionLog(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=ObjectId, alias="_id")
    game_id: PyObjectId
    player_id: PyObjectId
    action_type: str
    action_data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    client_ip: str
    device_fingerprint: Optional[str] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    } 