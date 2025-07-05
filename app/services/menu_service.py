from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime
import logging

from app.db.mongo import get_database
from app.models.menu import MenuMaster, MenuTree
from app.schemas.menu import MenuCreate, MenuUpdate, MenuResponse, MenuTreeResponse, MenuListResponse
from app.core.enums import Status, DeletionStatus

logger = logging.getLogger(__name__)

class MenuService:
    """Service for menu master operations"""
    
    def __init__(self):
        self.db = get_database()
        self.collection = self.db.menu_master
    
    async def create_menu(self, menu_data: MenuCreate, created_by: Optional[ObjectId] = None) -> MenuResponse:
        """Create a new menu item"""
        try:
            # Check if menu_value already exists
            existing_menu = await self.collection.find_one({
                "menu_value": menu_data.menu_value,
                "dels": DeletionStatus.NOT_DELETED
            })
            
            if existing_menu:
                raise ValueError(f"Menu with value '{menu_data.menu_value}' already exists")
            
            # Convert string parent_id to ObjectId if provided
            menu_dict = menu_data.model_dump()
            if menu_dict.get('fk_parent_id') and isinstance(menu_dict['fk_parent_id'], str):
                menu_dict['fk_parent_id'] = ObjectId(menu_dict['fk_parent_id'])
            
            # Create menu document
            menu_doc = MenuMaster(
                **menu_dict,
                created_by=created_by
            )
            
            # Insert into database
            result = await self.collection.insert_one(menu_doc.model_dump(by_alias=True))
            menu_doc.id = result.inserted_id
            
            logger.info(f"Created menu item: {menu_data.menu_value}")
            return MenuResponse(**menu_doc.model_dump())
            
        except Exception as e:
            logger.error(f"Error creating menu: {str(e)}")
            raise
    
    async def get_menu_by_id(self, menu_id: ObjectId) -> Optional[MenuResponse]:
        """Get menu item by ID"""
        try:
            menu_doc = await self.collection.find_one({
                "_id": menu_id,
                "dels": DeletionStatus.NOT_DELETED
            })
            
            if not menu_doc:
                return None
            
            return MenuResponse(**menu_doc)
            
        except Exception as e:
            logger.error(f"Error getting menu by ID: {str(e)}")
            raise
    
    async def get_menu_by_value(self, menu_value: str) -> Optional[MenuResponse]:
        """Get menu item by menu_value"""
        try:
            menu_doc = await self.collection.find_one({
                "menu_value": menu_value,
                "dels": DeletionStatus.NOT_DELETED
            })
            
            if not menu_doc:
                return None
            
            return MenuResponse(**menu_doc)
            
        except Exception as e:
            logger.error(f"Error getting menu by value: {str(e)}")
            raise
    
    async def update_menu(self, menu_id: ObjectId, menu_data: MenuUpdate, updated_by: Optional[ObjectId] = None) -> Optional[MenuResponse]:
        """Update an existing menu item"""
        try:
            # Check if menu exists
            existing_menu = await self.collection.find_one({
                "_id": menu_id,
                "dels": DeletionStatus.NOT_DELETED
            })
            
            if not existing_menu:
                return None
            
            # Check if menu_value is being changed and if it conflicts
            if menu_data.menu_value and menu_data.menu_value != existing_menu["menu_value"]:
                conflict_menu = await self.collection.find_one({
                    "menu_value": menu_data.menu_value,
                    "_id": {"$ne": menu_id},
                    "dels": DeletionStatus.NOT_DELETED
                })
                
                if conflict_menu:
                    raise ValueError(f"Menu with value '{menu_data.menu_value}' already exists")
            
            # Prepare update data
            update_data = menu_data.model_dump(exclude_unset=True)
            
            # Convert string parent_id to ObjectId if provided
            if update_data.get('fk_parent_id') and isinstance(update_data['fk_parent_id'], str):
                update_data['fk_parent_id'] = ObjectId(update_data['fk_parent_id'])
            
            update_data["updated_on"] = datetime.utcnow()
            if updated_by:
                update_data["updated_by"] = updated_by
            
            # Update in database
            result = await self.collection.update_one(
                {"_id": menu_id},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                return None
            
            # Get updated menu
            return await self.get_menu_by_id(menu_id)
            
        except Exception as e:
            logger.error(f"Error updating menu: {str(e)}")
            raise
    
    async def delete_menu(self, menu_id: ObjectId, deleted_by: Optional[ObjectId] = None) -> bool:
        """Soft delete a menu item"""
        try:
            # Check if menu has children
            children_count = await self.collection.count_documents({
                "fk_parent_id": menu_id,
                "dels": DeletionStatus.NOT_DELETED
            })
            
            if children_count > 0:
                raise ValueError("Cannot delete menu item with children. Delete children first.")
            
            # Soft delete
            result = await self.collection.update_one(
                {"_id": menu_id},
                {
                    "$set": {
                        "dels": DeletionStatus.DELETED,
                        "status": Status.INACTIVE,
                        "updated_on": datetime.utcnow(),
                        "updated_by": deleted_by
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting menu: {str(e)}")
            raise
    
    async def get_menus_by_type(self, menu_type: int, include_inactive: bool = False) -> List[MenuResponse]:
        """Get all menus of a specific type"""
        try:
            query = {"menu_type": menu_type}
            if not include_inactive:
                query.update({
                    "dels": DeletionStatus.NOT_DELETED,
                    "status": Status.ACTIVE
                })
            
            cursor = self.collection.find(query).sort("menu_order", 1)
            menus = await cursor.to_list(length=None)
            
            return [MenuResponse(**menu) for menu in menus]
            
        except Exception as e:
            logger.error(f"Error getting menus by type: {str(e)}")
            raise
    
    async def get_menu_tree(self, include_inactive: bool = False) -> List[MenuTreeResponse]:
        """Get hierarchical menu tree"""
        try:
            query = {}
            if not include_inactive:
                query.update({
                    "dels": DeletionStatus.NOT_DELETED,
                    "status": Status.ACTIVE
                })
            
            cursor = self.collection.find(query).sort("menu_order", 1)
            all_menus = await cursor.to_list(length=None)
            
            # Convert to MenuTree objects
            menu_dict: Dict[str, MenuTreeResponse] = {}
            root_menus: List[MenuTreeResponse] = []
            
            # First pass: create all menu objects
            for menu_data in all_menus:
                menu_tree = MenuTreeResponse(**menu_data)
                menu_dict[str(menu_tree.id)] = menu_tree
            
            # Second pass: build hierarchy
            for menu_tree in menu_dict.values():
                if menu_tree.fk_parent_id:
                    parent_id = str(menu_tree.fk_parent_id)
                    if parent_id in menu_dict:
                        menu_dict[parent_id].children.append(menu_tree)
                else:
                    root_menus.append(menu_tree)
            
            # Sort children by menu_order
            for menu_tree in menu_dict.values():
                menu_tree.children.sort(key=lambda x: x.menu_order)
            
            # Sort root menus by menu_order
            root_menus.sort(key=lambda x: x.menu_order)
            
            return root_menus
            
        except Exception as e:
            logger.error(f"Error getting menu tree: {str(e)}")
            raise
    
    async def get_menus_by_parent(self, parent_id: ObjectId, include_inactive: bool = False) -> List[MenuResponse]:
        """Get all child menus of a parent"""
        try:
            query = {"fk_parent_id": parent_id}
            if not include_inactive:
                query.update({
                    "dels": DeletionStatus.NOT_DELETED,
                    "status": Status.ACTIVE
                })
            
            cursor = self.collection.find(query).sort("menu_order", 1)
            menus = await cursor.to_list(length=None)
            
            return [MenuResponse(**menu) for menu in menus]
            
        except Exception as e:
            logger.error(f"Error getting menus by parent: {str(e)}")
            raise
    
    async def list_menus(
        self, 
        page: int = 1, 
        size: int = 10, 
        menu_type: Optional[int] = None,
        parent_id: Optional[ObjectId] = None,
        search: Optional[str] = None,
        include_inactive: bool = False
    ) -> MenuListResponse:
        """Get paginated list of menus with filters"""
        try:
            # Build query
            query = {}
            if not include_inactive:
                query.update({
                    "dels": DeletionStatus.NOT_DELETED,
                    "status": Status.ACTIVE
                })
            
            if menu_type is not None:
                query["menu_type"] = menu_type
            
            if parent_id is not None:
                query["fk_parent_id"] = parent_id
            
            if search:
                query["$or"] = [
                    {"menu_name": {"$regex": search, "$options": "i"}},
                    {"menu_value": {"$regex": search, "$options": "i"}},
                    {"description": {"$regex": search, "$options": "i"}}
                ]
            
            # Get total count
            total = await self.collection.count_documents(query)
            
            # Calculate pagination
            skip = (page - 1) * size
            pages = (total + size - 1) // size
            
            # Get paginated results
            cursor = self.collection.find(query).sort("menu_order", 1).skip(skip).limit(size)
            menus = await cursor.to_list(length=size)
            
            items = [MenuResponse(**menu) for menu in menus]
            
            return MenuListResponse(
                items=items,
                total=total,
                page=page,
                size=size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"Error listing menus: {str(e)}")
            raise
    
    async def reorder_menus(self, menu_orders: List[Dict[str, Any]]) -> bool:
        """Reorder menu items"""
        try:
            for order_data in menu_orders:
                menu_id = ObjectId(order_data["menu_id"])
                new_order = order_data["menu_order"]
                
                await self.collection.update_one(
                    {"_id": menu_id},
                    {"$set": {"menu_order": new_order, "updated_on": datetime.utcnow()}}
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error reordering menus: {str(e)}")
            raise
    
    async def get_menu_permissions(self, menu_value: str) -> Optional[Dict[str, Any]]:
        """Get permissions for a specific menu"""
        try:
            menu_doc = await self.collection.find_one({
                "menu_value": menu_value,
                "dels": DeletionStatus.NOT_DELETED,
                "status": Status.ACTIVE
            })
            
            if not menu_doc:
                return None
            
            return {
                "menu_id": str(menu_doc["_id"]),
                "menu_value": menu_doc["menu_value"],
                "can_view": bool(menu_doc["can_view"]),
                "can_add": bool(menu_doc["can_add"]),
                "can_edit": bool(menu_doc["can_edit"]),
                "can_delete": bool(menu_doc["can_delete"]),
                "active_urls": menu_doc["active_urls"]
            }
            
        except Exception as e:
            logger.error(f"Error getting menu permissions: {str(e)}")
            raise 