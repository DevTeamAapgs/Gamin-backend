from fastapi import APIRouter, HTTPException, Depends, Query, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from bson import ObjectId
import re
from datetime import datetime
import json

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.roles import (
    MenuItemModel, MenusubmenuAndPermission, PermissionSubmenuModel,  RolesModel, RoleCreate, RoleUpdate, RolePatch, RoleResponse,
    GridDataRequest, GridDataResponse, PermissionDetails
)
from app.models.menu import (
    MenuModel, MenuItem, MenuGroup, MenuQuery, PermissionSchema,
    MenuSchema, MenuPermissionSaveAction, PermissionsSchemaGridList
)
from app.auth.cookie_auth import verify_admin, get_current_user
from app.db.mongo import get_database
from app.core.enums import Status, DeletionStatus
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/roles", tags=["Roles"])
security = HTTPBearer()

# Constants
SORT_BY_DESC = -1
EMPLOYEE_SPECIAL_PERMISSION = ["dashboard", "profile", "settings"]  # Example special permissions

async def get_submenus(menu_id: str, db) -> List[PermissionSubmenuModel]:
    """Get submenus for a given menu ID"""
    pipeline = [
        {
            "$match": {
                "menu_type": 2,
                "fk_parent_id": ObjectId(menu_id),
            }
        },
        {
            "$sort": {"menu_order": 1},
        },
        {
            "$lookup": {
                "from": "menu_master",
                "localField": "_id",
                "foreignField": "fk_parent_id",
                "pipeline": [
                    {
                        "$sort": {"menu_order": 1},
                    }
                ],
                "as": "permissions",
            }
        },
    ]
    result = await db.menu_master.aggregate(pipeline).to_list()
    
    return   [PermissionSubmenuModel(**doc) for doc in result]

async def get_permissions(menu_id: str, db) -> List[Dict]:
    """Get permissions for a given menu ID"""
    pipeline = [
        {
            "$match": {
                "menu_type": 3,
                "fk_parent_id": ObjectId(menu_id),
            }
        },
        {
            "$sort": {"menu_order": 1},
        },
        {
            "$lookup": {
                "from": "menu_master",
                "localField": "_id",
                "foreignField": "fk_parent_id",
                "pipeline": [
                    {
                        "$sort": {"menu_order": 1},
                    }
                ],
                "as": "permissions",
            }
        },
    ]
    return await db.menu_master.aggregate(pipeline).to_list(length=None)

@router.get("/grid-data", response_model=GridDataResponse, tags=["Roles"])
async def get_grid_data(
    page: int = Query(1, description="Page number", ge=1),
    count: int = Query(10, description="Number of items per page", ge=1, le=100),
    searchString: Optional[str] = Query("", description="Search term for role name"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(verify_admin)
):
    """Get roles data for grid display with pagination and search"""
    try:
        
        # Use the query parameters directly
        search_term = searchString
        per_page = count
        
        # Build aggregation pipeline with facet for data and count
        pipeline = []
        
        # Add search filter if search term provided
        if search_term:
            pipeline.append({
                "$match": {
                    "$or": [{"role_name": {"$regex": re.escape(search_term), "$options": "i"}}]
                }
            })
        
        # Use facet to get both data and count in single query
        pipeline.append({
            "$facet": {
                "data": [
                    {"$sort": {"updated_on": SORT_BY_DESC}},
                    {"$project": {"_id": 1, "role_name": 1, "status": 1}},
                    {"$skip": (page - 1) * per_page},
                    {"$limit": per_page}
                ],
                "total": [
                    {"$count": "count"}
                ]
            }
        })
        
        # Execute aggregation
        result = await db.roles.aggregate(pipeline).to_list(length=1)
        facet_result = result[0] if result else {"data": [], "total": []}
        
        filtered_data = facet_result.get("data", [])
        total_count = facet_result.get("total", [{}])[0].get("count", 0) if facet_result.get("total") else 0


    
        # Convert to response format
        response_data = []
        for item in filtered_data:
            response_data.append({
                "id": str(item["_id"]),
                "role_name": item.get("role_name", ""),
                "status": item.get("status", Status.ACTIVE.value)
            })
        return GridDataResponse(
            data=response_data,
            total=total_count,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error getting grid data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get roles data")

@router.get("/get-form-dependency" , response_model=List[MenuItemModel])
@router.get("/get-form-dependency/{menu_id}",response_model=List[MenusubmenuAndPermission])
async def get_form_dependency(
    menu_id: Optional[str] = None,
    current_admin: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get form dependencies for role creation/editing"""
    try:
        response_data = []
        
        if menu_id:
            # Get specific menu permissions
            response_data.append({
                "id": menu_id,
                "menu_name": "UI.PARENT_DETAILS",
                "permissions": await get_permissions(menu_id, db)
            })
            response_data.extend(await get_submenus(menu_id, db))
            print(response_data,"response_data")
        else:
            # Get all menu structure
            pipeline = [
                {"$match": {"menu_type": 1}},
                {"$sort": {"menu_order": 1}},
                {"$sort": {"_id": 1}},
            ]
            response_data = await db.menu_master.aggregate(pipeline).to_list(length=None)
        return response_data
        
    except Exception as e:
        logger.error(f"Error getting form dependency: {e}")
        raise HTTPException(status_code=500, detail="Failed to get form dependency")

@router.post("", status_code=201)
async def create_role(
    role_data: RoleCreate,
    current_user: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Create a new role"""
    try:
        # Check if role already exists (without company filter)
        existing_role = await db.roles.find_one({
            "role_name": role_data.role_name
        })
        
        if existing_role:
            raise HTTPException(status_code=400, detail="Role already exists")
        
        # Create role using the model (without company ID)
        role = RolesModel(
            role_name=role_data.role_name,
            permissions=[]  # Will be set below
        )
        
        # Set permissions from dictionary
        role.set_permissions_from_dict(role_data.permissions)
        
        # Set audit fields for creation
        role.created_by = current_user.get("sub")
        role.updated_by = current_user.get("sub")
        
        # Insert into database
        print(role.model_dump(exclude={"id"}),"role")
        print(role.model_dump(),"role")
        result = await db.roles.insert_one(role.model_dump(exclude={"id"}))
        
        logger.info(f"Role created: {role_data.role_name} by {current_user.get('sub')}")
        
        return {"message": "Role created successfully", "id": str(result.inserted_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating role: {e}")
        raise HTTPException(status_code=500, detail="Failed to create role")

@router.put("")
async def update_role(
    role_data: RoleUpdate,
    current_user: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update an existing role"""
    try:
        role_id = ObjectId(role_data.id)
        
        # Check if role exists
        existing_role = await db.roles.find_one({"_id": role_id})
        if not existing_role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Create role model instance
        role = RolesModel(**existing_role)
        
        # Update role data
        role.role_name = role_data.role_name
        role.set_permissions_from_dict(role_data.permissions)
        
        # Update audit fields using the method
        role.update_audit_fields(updated_by=current_user.get("sub"))
        
        # Save to database
        await db.roles.update_one(
            {"_id": role_id}, 
            {"$set": role.model_dump(exclude={"id"})}
        )
        
        logger.info(f"Role updated: {role_data.role_name} by {current_user.get('sub')}")
        
        return {"message": "Role updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating role: {e}")
        raise HTTPException(status_code=500, detail="Failed to update role")

@router.patch("")
async def patch_role(
    role_data: RolePatch,
    current_user: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Patch role status"""
    try:
        role_id = ObjectId(role_data.id)
        
        # Check if role exists
        existing_role = await db.roles.find_one({"_id": role_id})
        if not existing_role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Create role model instance
        role = RolesModel(**existing_role)
        
        # Update status
        role.status = Status(role_data.status)
        
        # Update audit fields using the method
        role.update_audit_fields(updated_by=current_user.get("sub"))
        
        # Save to database
        await db.roles.update_one(
            {"_id": role_id}, 
            {"$set": {
                "status": role.status.value,
                "updated_on": role.updated_on,
                "updated_by": role.updated_by
            }}
        )
        
        logger.info(f"Role status updated: {role_data.id} by {current_user.get('sub')}")
        
        return {"message": "Role status updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error patching role: {e}")
        raise HTTPException(status_code=500, detail="Failed to update role status")

@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    current_user: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get a single role by ID"""
    try:
        role_doc = await db.roles.find_one({"_id": ObjectId(role_id)})
        if not role_doc:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Convert permissions list to nested dict
        nested_permissions = {}
        for permission in role_doc.get("permissions", []):
            module_id = permission["fk_module_id"]
            menu_id = permission["fk_menu_id"]
            can_access = permission["can_access"]
            
            if module_id not in nested_permissions:
                nested_permissions[module_id] = {}
            nested_permissions[module_id][menu_id] = can_access
        
        return RoleResponse(
            id=str(role_doc["_id"]),
            role_name=role_doc["role_name"],
            permissions=nested_permissions,
            status=role_doc.get("status", Status.ACTIVE.value),
            created_on=role_doc["created_on"],
            updated_on=role_doc["updated_on"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting role: {e}")
        raise HTTPException(status_code=500, detail="Failed to get role")

@router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    current_user: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete a role"""
    try:
        
        result = await db.roles.delete_one({"_id": ObjectId(role_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Role not found")
        
        logger.info(f"Role deleted: {role_id} by {current_user.get('sub')}")
        
        return {"message": "Role deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting role: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete role")

@router.delete("/bulk-delete/{role_ids}",dependencies=[Depends(verify_admin)])
async def bulk_delete_roles(
    role_ids: str,
    current_user: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Bulk delete roles"""
    try:
        # Parse role IDs
        ids_list = json.loads(role_ids)
        if not ids_list:
            raise HTTPException(status_code=400, detail="No role IDs provided")
        
        # Convert to ObjectIds
        object_ids = [ObjectId(role_id) for role_id in ids_list]
        
        # Delete roles
        result = await db.roles.delete_many({"_id": {"$in": object_ids}})
        
        logger.info(f"Bulk delete roles: {len(ids_list)} roles by {current_user.get('sub')}")
        
        return {"message": f"{result.deleted_count} roles deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk deleting roles: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete roles") 