from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, BeforeValidator
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

class PermissionDetails(BaseModel):
    """Permission details embedded document"""
    fk_module_id: str = Field(..., description="Module ID")
    fk_menu_id: str = Field(..., description="Menu ID")
    can_access: bool = Field(default=False, description="Access permission")
    
    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

class RolesModel(BaseDocument):
    """Roles model for managing user roles and permissions"""
    
    role_name: str = Field(..., description="Role name")
    permissions: List[PermissionDetails] = Field(default=[], description="List of permissions")
    
    model_config = {
        "collection": "roles",
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }
    
    def add_permission(self, module_id: str, menu_id: str, can_access: bool = True):
        """Add a permission to the role"""
        permission = PermissionDetails(
            fk_module_id=module_id,
            fk_menu_id=menu_id,
            can_access=can_access
        )
        self.permissions.append(permission)
    
    def remove_permission(self, module_id: str, menu_id: str):
        """Remove a permission from the role"""
        self.permissions = [
            p for p in self.permissions 
            if not (p.fk_module_id == module_id and p.fk_menu_id == menu_id)
        ]
    
    def has_permission(self, module_id: str, menu_id: str) -> bool:
        """Check if role has specific permission"""
        for permission in self.permissions:
            if permission.fk_module_id == module_id and permission.fk_menu_id == menu_id:
                return permission.can_access
        return False
    
    def get_permissions_dict(self) -> Dict[str, Dict[str, bool]]:
        """Get permissions as nested dictionary"""
        permissions_dict = {}
        for permission in self.permissions:
            if permission.fk_module_id not in permissions_dict:
                permissions_dict[permission.fk_module_id] = {}
            permissions_dict[permission.fk_module_id][permission.fk_menu_id] = permission.can_access
        return permissions_dict
    
    def set_permissions_from_dict(self, permissions_dict: Dict[str, Dict[str, bool]]):
        """Set permissions from nested dictionary"""
        self.permissions = []
        for module_id, menu_permissions in permissions_dict.items():
            for menu_id, can_access in menu_permissions.items():
                self.add_permission(module_id, menu_id, can_access)

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

class GridDataRequest(BaseModel):
    page: int = Field(..., description="Page number")
    count: int = Field(..., description="Items per page")
    searchString: str = Field(default="", description="Search string")

class GridDataItem(BaseModel):
    id: str = Field(..., description="Role ID")
    role_name: str = Field(..., description="Role name")
    status: int = Field(..., description="Status")

class GridDataResponse(BaseModel):
    data: List[GridDataItem] = Field(..., description="Role data")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Items per page") 






    
# class GetFormDependency(BaseModel):
class MenuItemModel(BaseModel):
    id: PyObjectId = Field(alias="_id")
    menu_order: Optional[int]
    menu_name: str
    menu_value: str
    menu_type: int
    fk_parent_id: Optional[Any] = None
    can_show: int
    router_url: str
    menu_icon: str
    active_urls: List[str]
    mobile_access: int
    menu_model: Optional[int] = None  # only in some entries

    class Config:
        populate_by_name  = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# Then define the main MenuItem model
class PermissionSubmenuModel(BaseModel):
    id: PyObjectId = Field(alias="_id")
    can_show: Optional[int] = None
    router_url: Optional[str] = None
    menu_icon: Optional[str] = None
    active_urls: Optional[List[str]] = None
    mobile_access: Optional[int] = None
    menu_model: Optional[int] = None
    menu_name: str
    menu_value: str
    menu_type: int
    fk_parent_id: PyObjectId
    menu_order: int
    description: Optional[str] = None
    permissions:Optional[List["PermissionSubmenuModel"]] = []  # Could be List['PermissionModel'] if recursive

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        populate_by_name=True
    )
PermissionSubmenuModel.model_rebuild()

class MenusubmenuAndPermission(BaseModel):
    id: str = Field(alias="id")
    menu_name: str
    can_show: Optional[int] = None
    router_url: Optional[str] = None
    menu_icon: Optional[str] = None
    active_urls: Optional[List[str]] = None
    mobile_access: Optional[int] = None
    menu_model: Optional[int] = None
    permissions: List[PermissionSubmenuModel]

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        populate_by_name=True
    )
