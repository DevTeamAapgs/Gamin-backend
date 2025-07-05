from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import Field
from bson import ObjectId
from app.models.base import BaseDocument, PyObjectId

class RequestLog(BaseDocument):
    """Request logging model with standardized audit fields"""
    player_id: Optional[PyObjectId] = None
    method: str
    path: str
    status_code: int
    client_ip: str
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None
    request_headers: Dict[str, str] = Field(default_factory=dict)
    response_headers: Dict[str, str] = Field(default_factory=dict)
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    process_time: float  # in seconds
    error_message: Optional[str] = None
    ttl: Optional[datetime] = None  # For automatic cleanup

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

class SecurityLog(BaseDocument):
    """Security logging model with standardized audit fields"""
    player_id: Optional[PyObjectId] = None
    event_type: str  # "failed_login", "suspicious_activity", "ban", "cheat_detected"
    client_ip: str
    device_fingerprint: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    severity: str = Field(default="info")  # "info", "warning", "error", "critical"
    ttl: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

class GameActionLog(BaseDocument):
    """Game action logging model with standardized audit fields"""
    game_id: PyObjectId
    player_id: PyObjectId
    action_type: str
    action_data: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None
    client_ip: str
    device_fingerprint: Optional[str] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    } 