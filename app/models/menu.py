from datetime import datetime
from typing import Optional, List, Any, Annotated
from pydantic import BaseModel, Field, BeforeValidator, ConfigDict
from bson import ObjectId
from app.models.base import BaseDocument, PyObjectId
from app.core.enums import Status, DeletionStatus

class MenuMaster(BaseDocument):
    """Menu Master model for hierarchical menu structure"""
    
    # Menu identification
    menu_name: str = Field(..., description="Display name for the menu item (e.g., 'UI.DASHBOARD')")
    menu_value: str = Field(..., description="Internal value/identifier for the menu item (e.g., 'dashboard')")
    menu_type: int = Field(..., description="Menu type: 1=Main menu, 2=Sub menu, 3=Action menu")
    menu_order: int = Field(..., description="Display order of the menu item")
    
    # Hierarchical relationship
    fk_parent_id: Optional[PyObjectId] = Field(None, description="Parent menu ID for sub-menus")
    
    # Display and access control
    can_show: int = Field(default=1, description="Whether menu item is visible (1=show, 0=hide)")
    router_url: str = Field(default="", description="Router URL for the menu item")
    menu_icon: str = Field(default="", description="Icon class/name for the menu item")
    
    # Active URLs for permission checking
    active_urls: List[str] = Field(default_factory=list, description="List of URLs that activate this menu item")
    
    # Access control
    mobile_access: int = Field(default=1, description="Mobile access permission (1=allowed, 0=denied)")
    
    # Permission flags for different actions
    can_view: int = Field(default=1, description="View permission (1=allowed, 0=denied)")
    can_add: int = Field(default=0, description="Add permission (1=allowed, 0=denied)")
    can_edit: int = Field(default=0, description="Edit permission (1=allowed, 0=denied)")
    can_delete: int = Field(default=0, description="Delete permission (1=allowed, 0=denied)")
    
    # Additional metadata
    description: Optional[str] = Field(None, description="Menu item description")
    module: Optional[str] = Field(None, description="Module this menu belongs to")
    
    model_config = {
        "collection_name": "menu_master",
        "indexes": [
            ("menu_value", 1),
            ("menu_type", 1),
            ("fk_parent_id", 1),
            ("menu_order", 1),
            ("status", 1),
            ("dels", 1)
        ]
    }

class MenuTree(BaseModel):
    """Menu tree structure for hierarchical display"""
    id: PyObjectId
    menu_name: str
    menu_value: str
    menu_type: int
    menu_order: int
    fk_parent_id: Optional[PyObjectId]
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
    children: List['MenuTree'] = Field(default_factory=list)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

# Update forward reference
MenuTree.model_rebuild() 