from gettext import find
from app.utils.upload_handler import move_file_from_temp_to_uploads
from unittest import result
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Body,Request
from bson import ObjectId, objectid
from enum import Enum
from app.core.enums import PlayerType
from typing import List, Optional, Dict, Any, Union, Annotated
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.enums import Status,PlayerType
from app.db.mongo import get_database
from app.auth.cookie_auth import verify_admin
from app.utils.prefix import generate_prefix
from app.utils.upload_handler import profile_pic_handler
from passlib.context import CryptContext
from datetime import datetime
from app.schemas.roles_schemas import GridDataItem
from app.schemas.admin_curd_schemas import AdminResponse, PaginationResponse, ListResponse,AdminIdResponse
from app.schemas.admin_curd_schemas import AdminStatusUpdateRequest, AdminCreateRequest, AdminUpdateRequest, AdminGetRequest
import logging
import traceback
from email_validator import validate_email, EmailNotValidError
from pathlib import Path
import shutil
from app.utils.pyobjectid import PyObjectId
from app.utils.crypto_dependencies import decrypt_body, decrypt_data_param

logger = logging.getLogger(__name__)
router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 1. GET /admins - List all admins
@router.get("/admins", response_model=ListResponse)
async def list_admins(
    params: dict = Depends(decrypt_data_param),
    #page: int = Query(1, ge=1),
    #count: int = Query(10, ge=1, le=100),
    #search_string: Optional[str] = Query(None),
    #status: Optional[int] = Query(None),
    #role: Optional[str] = Query(None),
    current_admin: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        page = int(params.get("page", 1))
        count = int(params.get("count", 10))
        search_string = params.get("search_string")
        status = params.get("status")
        role = params.get("role")
        query: Dict[str, Any] = {"player_type": PlayerType.ADMINEMPLOYEE}  # Allow both SUPERADMIN and ADMINEMPLOYEE
        print("search string ",params)
        
        if status is not None:
            try:
                status = int(status)
                query["is_active"] = bool(status)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid status parameter")
        
        if role:# Check if role is an ObjectId (role ID)
                try:
                    role_object_id = ObjectId(role)
                    # Direct comparison with fk_role_id
                    query["fk_role_id"] = role_object_id
                except Exception:
                    # If not an ObjectId, search by role name
                    role_doc = await db.roles.find_one({"role_name": role})
                    if role_doc:
                        query["fk_role_id"] = role_doc["_id"]
                    else:
                        return ListResponse(
                            data=[],
                            pagination=PaginationResponse(
                                page=page,
                                limit=count,
                                total=0,
                                pages=0,
                                has_next=False,
                                has_prev=False
                            )
                        )

        skip = (page - 1) * count
        
        pipeline = [
            {"$match": query},
            {
                "$lookup": {
                    "from": "roles",
                    "localField": "fk_role_id",
                    "foreignField": "_id",
                    "as": "role_info"
                }
            },
            {
                "$addFields": {
                    "role_name": {"$arrayElemAt": ["$role_info.role_name", 0]}
                }
            },
            {
                "$match": {
                    "$or": [
                        {"username": {"$regex": search_string, "$options": "i"}},
                        {"email": {"$regex": search_string, "$options": "i"}},
                        {"role_name": {"$regex": search_string, "$options": "i"}},
                    ]
                } if search_string else {}
            },
            {"$sort": {"updated_on": -1}},
            {"$skip": skip},
            {"$limit": count},
            {"$project": {"role_info": 0, "fk_role_id": 0  }}
        ]
        pipeline = [stage for stage in pipeline if stage != {"$match": {}}]

        total_query = query.copy()
        if search_string:
            total_query["$or"] = [
                {"username": {"$regex": search_string, "$options": "i"}},
                {"email": {"$regex": search_string, "$options": "i"}}
            ]

            matching_roles = await db.roles.find({
                "role_name": {"$regex": search_string, "$options": "i"}
            }).to_list(length=None)

            if matching_roles:
                role_ids = [role["_id"] for role in matching_roles]
                total_query["$or"].append({"fk_role_id": {"$in": role_ids}})

            # Get total count (outside aggregation)
        total = await db.players.count_documents(total_query)
        admin_list = await db.players.aggregate(pipeline).to_list(length=count)
        data = []
        for admin in admin_list:
            
            data.append(AdminResponse(
                id=str(admin["_id"]),
                username=admin["username"],
                email=admin.get("email", ""),
                status=admin.get("status", 1),
                role_name=admin.get("role_name"),
                profile_photo=admin.get("profile_photo")    
            ))
        print("data ",data)
        total_pages = (total + count - 1) // count
        return ListResponse(
            data=data,
            pagination=PaginationResponse(
                page=page,
                limit=count,
                total=total,
                pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1
            )
        )
        
    except Exception as e:
        logger.error(f"List admins failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list admins")

@router.get("/get-role-dependency",response_model=List[GridDataItem])
async def get_role_dependency(
   db: AsyncIOMotorDatabase = Depends(get_database), current_admin : dict = Depends(verify_admin)
):
    try: 
        print("current admin ",current_admin)
        role_docs = await db.roles.find({"status" :Status.ACTIVE.value }).to_list(length=None)
        result = []
        for item in role_docs:
            result.append(GridDataItem(
                id=str(item["_id"]),
                role_name=item.get("role_name", ""),
                status=item.get("status")
            ))
        return result
    except Exception as e:
        logger.error(f"List admins failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list roles") 
        
# 2.1. GET /admins/{admin_id} - Get specific admin by ID from URL parameter
@router.get("/admins/{admin_id}", response_model=AdminIdResponse)
async def get_admin_by_id(
    admin_id: str,  # Now a path parameter, not decrypted
    current_admin: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get a specific admin by ID from URL parameter."""
    try:
       
        result = await db.players.find_one({"_id": ObjectId(admin_id),"player_type": PlayerType.ADMINEMPLOYEE})
        if not result:
            raise HTTPException(status_code=404, detail="Admin not found")
        admin_data = result
        if not admin_data:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        
        return AdminIdResponse(
            id=str(admin_data["_id"]),
            username=admin_data["username"],
            email=admin_data.get("email", ""),
            status=admin_data.get("status", 1),
            profile_photo=admin_data.get("profile_photo"),
            fk_role_id=str(admin_data["fk_role_id"])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get admin failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get admin")

# 3. POST /admins - Create user
@router.post("/admins")
async def create_user(admin_data: AdminCreateRequest = Depends(decrypt_body(AdminCreateRequest)),
    current_admin: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        # Validate password
        if len(admin_data.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        # Validate email format
        if '@' not in admin_data.email or '.' not in admin_data.email.split('@')[1]:
            raise HTTPException(status_code=400, detail="Email must be a valid email address with a domain containing a dot (.)")
        
        # Validate role ID format
        try:
            role_object_id = ObjectId(admin_data.fk_role_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid role ID format: {admin_data.fk_role_id}")
        
        # Get role document
        role_doc = await db.roles.find_one({"_id": role_object_id})
        if not role_doc:
            raise HTTPException(status_code=400, detail=f"Role ID '{admin_data.fk_role_id}' not found")
        
        # Determine playertype and is_admin based on role name
        player_type = PlayerType.ADMINEMPLOYEE  # default to admin
        is_admin = True
        
        
        # Check for existing user (any playertype)
        existing_user = await db.players.find_one({
            "$or": [{"username": admin_data.username}, {"email": admin_data.email}]
        })
        if existing_user:
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        # Generate unique fields
        created_at = datetime.utcnow()
        
        # Ensure current_admin has username
        if not current_admin.get("username"):
            raise HTTPException(status_code=400, detail="Current admin username is missing. Cannot set created_by/updated_by.")
        
        # Handle profile picture if provided
        profile_photo = None
        if admin_data.profile_photo:
            profile_photo = move_file_from_temp_to_uploads(admin_data.profile_photo)
        
        # Create user document
        user_doc = {
            "username": admin_data.username,
            "email": admin_data.email,
            "password_hash": get_password_hash(admin_data.password),
            "fk_role_id": role_object_id,
            "rolename": role_doc.get("role_name", ""),
            "player_type": player_type,
            "is_admin": is_admin,
            "is_active": True,
            "is_verified": True,
            "created_at": created_at,
            "created_on": created_at,
            "updated_on": created_at,
            "created_by": ObjectId(current_admin.get("_id")),
            "updated_by": ObjectId(current_admin.get("_id")),
            "status": 1,
            "dels": 0,
            "last_login": None
        }
        
        # Add profile photo if provided
        if profile_photo:
            user_doc["profile_photo"] = profile_photo
        
        await db.players.insert_one(user_doc)
        return {"message": "Admin created successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create admin failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create admin: {str(e)}")

# 4. PUT /admins - Update admin with ID in JSON body
@router.put("/admins")
async def update_admin(    admin_data: AdminUpdateRequest = Depends(decrypt_body(AdminUpdateRequest)),
    current_admin: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update an admin user."""
    try:
        admin_id = admin_data.id
        # Check if admin exists (SUPERADMIN or ADMINEMPLOYEE)
        existing_user = await db.players.find_one({"_id": ObjectId(admin_id), "player_type": PlayerType.ADMINEMPLOYEE})
        if not existing_user:
                logger.warning(f"User {admin_id} not found")
                raise HTTPException(status_code=404, detail="Admin not found")
        
        logger.info(f"Updating admin {admin_id} with data: {admin_data}")
        logger.info(f"Current admin: {current_admin.get('username')} (ID: {current_admin.get('_id')})")
        
        # Validate password if provided
        if admin_data.password and len(admin_data.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
        
        # Validate email format if provided
        if admin_data.email and ('@' not in admin_data.email or '.' not in admin_data.email.split('@')[1]):
            raise HTTPException(status_code=400, detail="Email must be a valid email address with a domain containing a dot (.)")
        
        # Check for duplicate username/email (any playertype)
        if admin_data.username or admin_data.email:
    # Build OR conditions
            or_conditions = []
            if admin_data.username:
                or_conditions.append({"username": admin_data.username})
            if admin_data.email:
                or_conditions.append({"email": admin_data.email})

            # Build final query excluding current user
            query = {
                "_id": {"$ne": ObjectId(admin_id)},
                "$or": or_conditions
            }

            duplicate_user = await db.players.find_one(query)

            if duplicate_user:
                if admin_data.username and duplicate_user.get("username") == admin_data.username:
                    logger.warning(f"Username '{admin_data.username}' already exists for user {duplicate_user['_id']}")
                    raise HTTPException(status_code=400, detail="Username already exists")
                if admin_data.email and duplicate_user.get("email") == admin_data.email:
                    logger.warning(f"Email '{admin_data.email}' already exists for user {duplicate_user['_id']}")
                    raise HTTPException(status_code=400, detail="Email already exists")

        # Determine new playertype and is_admin if role is provided
        new_playertype = existing_user.get("player_type", PlayerType.ADMINEMPLOYEE)  # Keep existing if no role change
        new_is_admin = existing_user.get("is_admin", True)   # Keep existing if no role change
        
        # Get role document if role is provided
        role_doc = None
        if admin_data.fk_role_id:
            try:
                role_object_id = ObjectId(admin_data.fk_role_id)
                role_doc = await db.roles.find_one({"_id": role_object_id})
                if not role_doc:
                    raise HTTPException(status_code=400, detail=f"Role ID '{admin_data.fk_role_id}' not found")
                
                # Update playertype and is_admin based on new role name
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid role ID format: {admin_data.fk_role_id}")
        
        # Handle profile picture
        profile_photo = None  # Default to None (no profile photo)
        if admin_data.profile_photo:
            profile_photo = move_file_from_temp_to_uploads(admin_data.profile_photo)
        else:
            # No profile photo provided - delete existing one if it exists
            if existing_user.get("profile_photo"):
                try:
                    old_file_path = existing_user["profile_photo"]["uploadurl"]
                    deleted = profile_pic_handler.delete_file_by_path(old_file_path)
                    if deleted:
                        logger.info(f"Profile picture deleted: {old_file_path}")
                    else:
                        logger.warning(f"Profile picture file not found: {old_file_path}")
                except Exception as e:
                    logger.error(f"Error deleting profile picture: {e}")
                
        
        # Build update data
        update_data = {
            "updated_on": datetime.utcnow(),
            "updated_by": current_admin.get("_id"),
            "player_type": new_playertype,
            "is_admin": new_is_admin
        }
        if admin_data.username:
            update_data["username"] = admin_data.username
        if admin_data.email:
            update_data["email"] = admin_data.email
        if admin_data.password:
            update_data["password_hash"] = get_password_hash(admin_data.password)
        if role_doc:
            update_data["fk_role_id"] = role_doc["_id"]
            update_data["rolename"] = role_doc.get("role_name", "")
        # Always include profile_photo in update (either new value or None to remove)
        update_data["profile_photo"] = profile_photo
        
        # Update user
        await db.players.update_one(
            {"_id": ObjectId(admin_id)},
            {"$set": update_data}
        )
        
        logger.info(f"User updated: {admin_id}")
        
        return {"message": "Admin updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update admin failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Handle MongoDB duplicate key errors specifically
        if "duplicate key error" in str(e) and "email" in str(e):
            raise HTTPException(status_code=400, detail="Email already exists")
        elif "duplicate key error" in str(e) and "username" in str(e):
            raise HTTPException(status_code=400, detail="Username already exists")
        
        raise HTTPException(status_code=500, detail="Failed to update admin")

# 5. PATCH /admins/status - Update admin status
@router.patch("/admins/status")
async def update_admin_status(
    status_data: AdminStatusUpdateRequest = Depends(decrypt_body(AdminStatusUpdateRequest)),
    current_admin: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update admin status."""
    try:
        admin_id = status_data.id
        print("admin_id ",admin_id)
        print("status_data ",status_data)
        # Check if admin exists
        existing_admin = await db.players.find_one({"_id": ObjectId(admin_id), "player_type": PlayerType.ADMINEMPLOYEE})
        print(existing_admin,"existing_admin")
        if not existing_admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        # Update status
        is_active = status_data.status == 1
        update_data = {
            "status": status_data.status,
            "is_active": is_active,
            "updated_on": datetime.utcnow(),
            "updated_by": current_admin.get("_id")
        }
        
        await db.players.update_one(
            {"_id": ObjectId(admin_id)},
            {"$set": update_data}
        )
        
        logger.info(f"Admin status updated: {admin_id} to status {status_data.status}")
        
        return {"message": "Admin status updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update admin status failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to update admin status")

# 6. DELETE /admins - Delete admin by ID from JSON body
@router.delete("/admins")
async def delete_admin(
    admin_data: AdminGetRequest = Depends(decrypt_body(AdminGetRequest)),
    current_admin: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete an admin user."""
    try:
        admin_id = admin_data.admin_id
        # Check if admin exists
        existing_admin = await db.players.find_one({"_id": ObjectId(admin_id), "player_type": PlayerType.ADMINEMPLOYEE})
        if not existing_admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        # Delete profile picture if exists
        if existing_admin.get("profile_photo"):
            try:
                # Use the delete_file_by_path method which handles file paths/URLs
                file_path = existing_admin["profile_photo"]["uploadurl"]
                deleted = profile_pic_handler.delete_file_by_path(file_path)
                if deleted:
                    logger.info(f"Profile picture deleted for admin {admin_id}: {file_path}")
                else:
                    logger.warning(f"Profile picture file not found for admin {admin_id}: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting profile picture for admin {admin_id}: {e}")
                # Continue with admin deletion even if file deletion fails
        
        # Delete admin
        result = await db.players.delete_one({"_id": ObjectId(admin_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        logger.info(f"Admin deleted: {admin_id}")
        
        return {"message": "Admin deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete admin failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete admin")

