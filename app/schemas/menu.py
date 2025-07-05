from datetime import datetime
from typing import Optional, List, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from app.models.base import PyObjectId

class MenuCreate(BaseModel):
    """Schema for creating a new menu item"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    menu_name: str = Field(..., description="Display name for the menu item")
    menu_value: str = Field(..., description="Internal value/identifier for the menu item")
    menu_type: int = Field(..., description="Menu type: 1=Main menu, 2=Sub menu, 3=Action menu")
    menu_order: int = Field(..., description="Display order of the menu item")
    fk_parent_id: Optional[Union[str, PyObjectId]] = Field(None, description="Parent menu ID for sub-menus")
    can_show: int = Field(default=1, description="Whether menu item is visible")
    router_url: str = Field(default="", description="Router URL for the menu item")
    menu_icon: str = Field(default="", description="Icon class/name for the menu item")
    active_urls: List[str] = Field(default_factory=list, description="List of URLs that activate this menu item")
    mobile_access: int = Field(default=1, description="Mobile access permission")
    can_view: int = Field(default=1, description="View permission")
    can_add: int = Field(default=0, description="Add permission")
    can_edit: int = Field(default=0, description="Edit permission")
    can_delete: int = Field(default=0, description="Delete permission")
    description: Optional[str] = Field(None, description="Menu item description")
    module: Optional[str] = Field(None, description="Module this menu belongs to")

class MenuUpdate(BaseModel):
    """Schema for updating an existing menu item"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    menu_name: Optional[str] = Field(None, description="Display name for the menu item")
    menu_value: Optional[str] = Field(None, description="Internal value/identifier for the menu item")
    menu_type: Optional[int] = Field(None, description="Menu type: 1=Main menu, 2=Sub menu, 3=Action menu")
    menu_order: Optional[int] = Field(None, description="Display order of the menu item")
    fk_parent_id: Optional[Union[str, PyObjectId]] = Field(None, description="Parent menu ID for sub-menus")
    can_show: Optional[int] = Field(None, description="Whether menu item is visible")
    router_url: Optional[str] = Field(None, description="Router URL for the menu item")
    menu_icon: Optional[str] = Field(None, description="Icon class/name for the menu item")
    active_urls: Optional[List[str]] = Field(None, description="List of URLs that activate this menu item")
    mobile_access: Optional[int] = Field(None, description="Mobile access permission")
    can_view: Optional[int] = Field(None, description="View permission")
    can_add: Optional[int] = Field(None, description="Add permission")
    can_edit: Optional[int] = Field(None, description="Edit permission")
    can_delete: Optional[int] = Field(None, description="Delete permission")
    description: Optional[str] = Field(None, description="Menu item description")
    module: Optional[str] = Field(None, description="Module this menu belongs to")

class MenuResponse(BaseModel):
    """Schema for menu response"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: str
    menu_name: str
    menu_value: str
    menu_type: int
    menu_order: int
    fk_parent_id: Optional[str]
    can_show: int
    router_url: str
    menu_icon: str
    active_urls: List[str]
    mobile_access: int
    can_view: int
    can_add: int
    can_edit: int
    can_delete: int
    description: Optional[str]
    module: Optional[str]
    created_on: datetime
    updated_on: datetime
    created_by: Optional[str]
    updated_by: Optional[str]
    status: int
    dels: int

class MenuTreeResponse(BaseModel):
    """Schema for hierarchical menu tree response"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: str
    menu_name: str
    menu_value: str
    menu_type: int
    menu_order: int
    fk_parent_id: Optional[str]
    can_show: int
    router_url: str
    menu_icon: str
    active_urls: List[str]
    mobile_access: int
    can_view: int
    can_add: int
    can_edit: int
    can_delete: int
    description: Optional[str]
    module: Optional[str]
    children: List['MenuTreeResponse'] = Field(default_factory=list)

# Update forward reference
MenuTreeResponse.model_rebuild()

class MenuListResponse(BaseModel):
    """Schema for paginated menu list response"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    items: List[MenuResponse]
    total: int
    page: int
    size: int
    pages: int

class MenuPermissionResponse(BaseModel):
    """Schema for menu permissions response"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    menu_id: str
    menu_value: str
    can_view: bool
    can_add: bool
    can_edit: bool
    can_delete: bool
    active_urls: List[str] 