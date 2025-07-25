from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, BeforeValidator
from bson import ObjectId
from app.models.base import BaseDocument
from app.core.enums import Status, DeletionStatus
from app.utils.pyobjectid import PyObjectId


class RoleResponse(BaseModel):
    id: str = Field(..., description="Role ID")
    role_name: str = Field(..., description="Role name")
    permissions: Dict[str, Dict[str, bool]] = Field(default={}, description="Permissions dictionary")
    status: int = Field(..., description="Status")
    created_on: datetime = Field(..., description="Created date")
    updated_on: datetime = Field(..., description="Updated date")
    
    model_config = {
        "json_encoders": {ObjectId: str}
    }


class GridDataItem(BaseModel):
    id: str = Field(..., description="Role ID")
    role_name: str = Field(..., description="Role name")
    status: int = Field(..., description="Status")

class GridDataResponse(BaseModel):
    data: List[GridDataItem] = Field(..., description="Role data")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Items per page") 


# Pydantic models for API requests/responses
class RoleCreate(BaseModel):
    role_name: str = Field(..., description="Role name")
    permissions: Dict[str, Dict[str, bool]] = Field(default={}, description="Permissions dictionary")

class RoleUpdate(BaseModel):
    id: str = Field(..., description="Role ID")
    role_name: str = Field(..., description="Role name")
    permissions: Dict[str, Dict[str, bool]] = Field(default={}, description="Permissions dictionary")

class RolePatch(BaseModel):
    id: str = Field(..., description="Role ID")
    status: int = Field(..., description="Status (0=inactive, 1=active)")



class GridDataRequest(BaseModel):
    page: int = Field(..., description="Page number")
    count: int = Field(..., description="Items per page")
    searchString: str = Field(default="", description="Search string")




