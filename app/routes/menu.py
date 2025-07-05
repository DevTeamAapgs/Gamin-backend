from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import List, Optional
from bson import ObjectId
import logging

from app.services.menu_service import MenuService
from app.schemas.menu import (
    MenuCreate, 
    MenuUpdate, 
    MenuResponse, 
    MenuTreeResponse, 
    MenuListResponse,
    MenuPermissionResponse
)
from app.auth.cookie_auth import get_current_user
from app.models.player import Player

logger = logging.getLogger(__name__)

router = APIRouter()

def get_menu_service() -> MenuService:
    """Dependency to get menu service instance"""
    return MenuService()

@router.post("/", response_model=MenuResponse, summary="Create Menu Item")
async def create_menu(
    menu_data: MenuCreate,
    menu_service: MenuService = Depends(get_menu_service),
    current_user: Player = Depends(get_current_user)
):
    """
    Create a new menu item.
    
    - **menu_name**: Display name for the menu item (e.g., 'UI.DASHBOARD')
    - **menu_value**: Internal value/identifier for the menu item (e.g., 'dashboard')
    - **menu_type**: Menu type (1=Main menu, 2=Sub menu, 3=Action menu)
    - **menu_order**: Display order of the menu item
    - **fk_parent_id**: Parent menu ID for sub-menus (optional)
    - **can_show**: Whether menu item is visible (1=show, 0=hide)
    - **router_url**: Router URL for the menu item
    - **menu_icon**: Icon class/name for the menu item
    - **active_urls**: List of URLs that activate this menu item
    - **mobile_access**: Mobile access permission (1=allowed, 0=denied)
    - **can_view**: View permission (1=allowed, 0=denied)
    - **can_add**: Add permission (1=allowed, 0=denied)
    - **can_edit**: Edit permission (1=allowed, 0=denied)
    - **can_delete**: Delete permission (1=allowed, 0=denied)
    """
    try:
        return await menu_service.create_menu(menu_data, created_by=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating menu: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{menu_id}", response_model=MenuResponse, summary="Get Menu by ID")
async def get_menu(
    menu_id: str = Path(..., description="Menu ID"),
    menu_service: MenuService = Depends(get_menu_service),
    current_user: Player = Depends(get_current_user)
):
    """Get a menu item by its ID."""
    try:
        menu = await menu_service.get_menu_by_id(ObjectId(menu_id))
        if not menu:
            raise HTTPException(status_code=404, detail="Menu not found")
        return menu
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid menu ID format")
    except Exception as e:
        logger.error(f"Error getting menu: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/value/{menu_value}", response_model=MenuResponse, summary="Get Menu by Value")
async def get_menu_by_value(
    menu_value: str = Path(..., description="Menu value/identifier"),
    menu_service: MenuService = Depends(get_menu_service),
    current_user: Player = Depends(get_current_user)
):
    """Get a menu item by its menu_value."""
    try:
        menu = await menu_service.get_menu_by_value(menu_value)
        if not menu:
            raise HTTPException(status_code=404, detail="Menu not found")
        return menu
    except Exception as e:
        logger.error(f"Error getting menu by value: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{menu_id}", response_model=MenuResponse, summary="Update Menu")
async def update_menu(
    menu_data: MenuUpdate,
    menu_id: str = Path(..., description="Menu ID"),
    menu_service: MenuService = Depends(get_menu_service),
    current_user: Player = Depends(get_current_user)
):
    """Update an existing menu item."""
    try:
        menu = await menu_service.update_menu(ObjectId(menu_id), menu_data, updated_by=current_user.id)
        if not menu:
            raise HTTPException(status_code=404, detail="Menu not found")
        return menu
    except ValueError as e:
        if "Invalid" in str(e):
            raise HTTPException(status_code=400, detail="Invalid menu ID format")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating menu: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{menu_id}", summary="Delete Menu")
async def delete_menu(
    menu_id: str = Path(..., description="Menu ID"),
    menu_service: MenuService = Depends(get_menu_service),
    current_user: Player = Depends(get_current_user)
):
    """Soft delete a menu item."""
    try:
        success = await menu_service.delete_menu(ObjectId(menu_id), deleted_by=current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Menu not found")
        return {"message": "Menu deleted successfully"}
    except ValueError as e:
        if "Invalid" in str(e):
            raise HTTPException(status_code=400, detail="Invalid menu ID format")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting menu: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/type/{menu_type}", response_model=List[MenuResponse], summary="Get Menus by Type")
async def get_menus_by_type(
    menu_type: int = Path(..., description="Menu type (1=Main, 2=Sub, 3=Action)"),
    include_inactive: bool = Query(False, description="Include inactive menus"),
    menu_service: MenuService = Depends(get_menu_service),
    current_user: Player = Depends(get_current_user)
):
    """Get all menus of a specific type."""
    try:
        return await menu_service.get_menus_by_type(menu_type, include_inactive)
    except Exception as e:
        logger.error(f"Error getting menus by type: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/tree/hierarchy", response_model=List[MenuTreeResponse], summary="Get Menu Tree")
async def get_menu_tree(
    include_inactive: bool = Query(False, description="Include inactive menus"),
    menu_service: MenuService = Depends(get_menu_service),
    current_user: Player = Depends(get_current_user)
):
    """Get hierarchical menu tree structure."""
    try:
        return await menu_service.get_menu_tree(include_inactive)
    except Exception as e:
        logger.error(f"Error getting menu tree: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/parent/{parent_id}", response_model=List[MenuResponse], summary="Get Child Menus")
async def get_menus_by_parent(
    parent_id: str = Path(..., description="Parent menu ID"),
    include_inactive: bool = Query(False, description="Include inactive menus"),
    menu_service: MenuService = Depends(get_menu_service),
    current_user: Player = Depends(get_current_user)
):
    """Get all child menus of a parent menu."""
    try:
        return await menu_service.get_menus_by_parent(ObjectId(parent_id), include_inactive)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid parent ID format")
    except Exception as e:
        logger.error(f"Error getting menus by parent: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/", response_model=MenuListResponse, summary="List Menus")
async def list_menus(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    menu_type: Optional[int] = Query(None, description="Filter by menu type"),
    parent_id: Optional[str] = Query(None, description="Filter by parent ID"),
    search: Optional[str] = Query(None, description="Search in menu name, value, or description"),
    include_inactive: bool = Query(False, description="Include inactive menus"),
    menu_service: MenuService = Depends(get_menu_service),
    current_user: Player = Depends(get_current_user)
):
    """
    Get paginated list of menus with optional filters.
    
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 10, max: 100)
    - **menu_type**: Filter by menu type (1=Main, 2=Sub, 3=Action)
    - **parent_id**: Filter by parent menu ID
    - **search**: Search term for menu name, value, or description
    - **include_inactive**: Include inactive menus in results
    """
    try:
        parent_obj_id = ObjectId(parent_id) if parent_id else None
        return await menu_service.list_menus(
            page=page,
            size=size,
            menu_type=menu_type,
            parent_id=parent_obj_id,
            search=search,
            include_inactive=include_inactive
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid parent ID format")
    except Exception as e:
        logger.error(f"Error listing menus: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/reorder", summary="Reorder Menus")
async def reorder_menus(
    menu_orders: List[dict],
    menu_service: MenuService = Depends(get_menu_service),
    current_user: Player = Depends(get_current_user)
):
    """
    Reorder menu items.
    
    Expected format:
    ```json
    [
        {"menu_id": "menu_id_1", "menu_order": 1},
        {"menu_id": "menu_id_2", "menu_order": 2}
    ]
    ```
    """
    try:
        # Validate and convert menu_ids to ObjectId
        for order_data in menu_orders:
            if 'menu_id' not in order_data or 'menu_order' not in order_data:
                raise HTTPException(status_code=400, detail="Each menu order must contain 'menu_id' and 'menu_order'")
            try:
                order_data['menu_id'] = ObjectId(order_data['menu_id'])
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail="Invalid menu ID format")
        
        success = await menu_service.reorder_menus(menu_orders)
        if success:
            return {"message": "Menus reordered successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to reorder menus")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reordering menus: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/permissions/{menu_value}", response_model=MenuPermissionResponse, summary="Get Menu Permissions")
async def get_menu_permissions(
    menu_value: str = Path(..., description="Menu value/identifier"),
    menu_service: MenuService = Depends(get_menu_service),
    current_user: Player = Depends(get_current_user)
):
    """Get permissions for a specific menu item."""
    try:
        permissions = await menu_service.get_menu_permissions(menu_value)
        if not permissions:
            raise HTTPException(status_code=404, detail="Menu not found")
        return MenuPermissionResponse(**permissions)
    except Exception as e:
        logger.error(f"Error getting menu permissions: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/main-menu", response_model=List[MenuResponse], summary="Get Main Menu Items")
async def get_main_menu(
    menu_service: MenuService = Depends(get_menu_service),
    current_user: Player = Depends(get_current_user)
):
    """Get all main menu items (menu_type = 1)."""
    try:
        return await menu_service.get_menus_by_type(1, include_inactive=False)
    except Exception as e:
        logger.error(f"Error getting main menu: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") 