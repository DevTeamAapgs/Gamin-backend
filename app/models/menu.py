from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, BeforeValidator
from bson import ObjectId
from app.models.base import BaseDocument
from app.core.enums import Status, DeletionStatus
from app.utils.pyobjectid import PyObjectId

def validate_object_id(v: Any) -> ObjectId:
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str):
        if ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId string")
    raise ValueError("Invalid ObjectId")

class MenuModel(BaseDocument):
    """Menu model for managing application menus and permissions"""
    
    menu_name: str = Field(..., description="Menu name")
    menu_value: str = Field(..., description="Menu value/identifier")
    menu_type: int = Field(..., description="Menu type (1=module, 2=submenu, 3=permission)")
    menu_model: int = Field(..., description="Menu model/group")
    menu_order: int = Field(default=0, description="Menu display order")
    fk_parent_id: Optional[PyObjectId] = Field(default=None, description="Parent menu ID")
    description: Optional[str] = Field(default=None, description="Menu description")
    
    model_config = {
        "collection": "menu_master",
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

# Pydantic models for API requests/responses
class MenuItem(BaseModel):
    id: str = Field(..., description="Menu ID")
    menu_name: str = Field(..., description="Menu name")
    menu_value: str = Field(..., description="Menu value")
    menu_type: int = Field(..., description="Menu type")
    menu_model: int = Field(..., description="Menu model")
    menu_order: int = Field(..., description="Menu order")
    fk_parent_id: Optional[str] = Field(default=None, description="Parent menu ID")
    description: Optional[str] = Field(default=None, description="Menu description")
    permissions: List['MenuItem'] = Field(default=[], description="Sub-permissions")
    
    model_config = {
        "json_encoders": {ObjectId: str}
    }

class MenuGroup(BaseModel):
    id: int = Field(..., description="Menu model/group ID")
    menu_items: List[MenuItem] = Field(..., description="Menu items in this group")

class MenuQuery(BaseModel):
    id: str = Field(..., description="Menu ID")
    menu_name: str = Field(..., description="Menu name")
    menu_value: str = Field(..., description="Menu value")
    menu_type: int = Field(..., description="Menu type")
    menu_model: int = Field(..., description="Menu model")
    menu_order: int = Field(..., description="Menu order")
    fk_parent_id: str = Field(..., description="Parent menu ID")
    description: Optional[str] = Field(default=None, description="Menu description")
    
    model_config = {
        "json_encoders": {ObjectId: str}
    }

class PermissionSchema(BaseModel):
    id: str = Field(..., description="Permission ID")
    menu_name: str = Field(..., description="Menu name")
    menu_value: str = Field(..., description="Menu value")
    menu_type: int = Field(..., description="Menu type")
    menu_model: int = Field(..., description="Menu model")
    menu_order: int = Field(..., description="Menu order")
    fk_parent_id: str = Field(..., description="Parent menu ID")
    description: Optional[str] = Field(default=None, description="Menu description")
    permissions: List['PermissionSchema'] = Field(default=[], description="Sub-permissions")
    
    model_config = {
        "json_encoders": {ObjectId: str}
    }

class MenuSchema(BaseModel):
    id: int = Field(..., description="Menu model/group ID")
    menu_items: List[MenuItem] = Field(..., description="Menu items in this group")

class MenuPermissionSaveAction(BaseModel):
    role_name: str = Field(..., description="Role name")
    permissions: Dict[str, Dict[str, bool]] = Field(default={}, description="Permissions dictionary")

class PermissionsSchemaGridList(BaseModel):
    id: str = Field(..., description="Role ID")
    role_name: str = Field(..., description="Role name")
    status: int = Field(..., description="Status")
    
    model_config = {
        "json_encoders": {ObjectId: str}
    } 

class MenuCard(BaseModel):
    _id: str
    menu_order: int
    menu_name: str
    menu_value: str
    menu_type: int
    fk_parent_id: Optional[str]
    can_show: int
    router_url: str
    menu_icon: str
    active_urls: List[str]
    mobile_access: int 