from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from bson import ObjectId
from datetime import datetime
from app.db.mongo import get_database
from app.auth.cookie_auth import get_current_user
from app.utils.upload_handler import FileUploadHandler
import logging
from app.models.player import Player
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)
router = APIRouter()
file_handler = FileUploadHandler()

# POST /common/file-upload - Upload file
@router.post("/common/file-upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: Player = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Upload file for the current user.
    
    File size limit: 5MB
    Allowed file types: jpg, jpeg, png, gif, bmp, webp
    """
    try:
        # Get current user's ID
        user_id = str(current_user.id)
        
        # Check if user exists
        existing_user = await db.players.find_one({"_id": ObjectId(user_id)})
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Clean up previous temp files for this user before uploading new one
        #await cleanup_user_temp_files(user_id, existing_user)
        
        # Upload file to temp_uploads (includes 5MB size validation)
        file_info = await file_handler.upload_to_temp(file, user_id)
        
        logger.info(f"File uploaded to temp by user: {user_id}")
        
        return file_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload file failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")

async def cleanup_user_temp_files(user_id: str, existing_user: dict):
    """Clean up orphaned temp files for a user."""
    try:
        # Get user's current profile photo
        current_profile_photo = existing_user.get("profile_photo", {})
        current_uploadurl = current_profile_photo.get("uploadurl") if current_profile_photo else None
        
        # Get all files in temp_uploads that belong to this user
        temp_dir = Path("temp_uploads")
        if not temp_dir.exists():
            return
        
        user_temp_files = []
        deleted_files = []
        
        # Find all temp files for this user
        for temp_file in temp_dir.glob(f"profile_{user_id}_*"):
            if temp_file.is_file():
                user_temp_files.append(str(temp_file))
        
        if not user_temp_files:
            return
        
        logger.info(f"Found {len(user_temp_files)} temp files for user {user_id}: {user_temp_files}")
        
        # Delete files that are not the current profile photo
        for file_path in user_temp_files:
            # Convert temp path to uploads path for comparison
            file_name = Path(file_path).name
            file_url_path = f"public/uploads/{file_name}"
            
            # Skip if this is the current profile photo
            if file_url_path == current_uploadurl:
                logger.info(f"Skipping current profile photo: {file_path}")
                continue
            
            # Delete the orphaned file using the upload handler
            try:
                deleted = file_handler.delete_file_by_path(file_path)
                if deleted:
                    deleted_files.append(file_path)
                    logger.info(f"Deleted orphaned temp file: {file_path}")
                else:
                    logger.warning(f"Failed to delete temp file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete temp file {file_path}: {e}")
        
        if deleted_files:
            logger.info(f"Cleaned up {len(deleted_files)} orphaned temp files for user: {user_id}")
        
    except Exception as e:
        logger.error(f"Error cleaning up temp files for user {user_id}: {e}")

# DELETE /common/file-upload - Delete file
@router.delete("/common/file-upload")
async def delete_file(
    file_url_path: str,
    current_user: Player = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    print(Path("public/uploads/file_686b92d57248234e88b16a60_ae41d855.png").exists())
    print(file_url_path)
    print(Path(file_url_path).exists())
    """Delete file for the current user."""
    try:
        # Get current user's ID
        user_id = str(current_user.id)
        
        # Check if user exists
        existing_user = await db.players.find_one({"_id": ObjectId(user_id)})
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Extract filename from file_url_path
        # file_url_path format: "public/uploads/filename.ext" or "public/temp_uploads/filename.ext"
        logger.info(f"Received file_url_path: '{file_url_path}'")
        
        # Normalize the path (remove any leading/trailing whitespace)
        file_url_path = file_url_path.strip()
        
        if not (file_url_path.startswith("public/uploads/") or file_url_path.startswith("public/temp_uploads/")):
            logger.error(f"Invalid file URL path format: '{file_url_path}'")
            raise HTTPException(status_code=400, detail=f"Invalid file URL path format. Must start with 'public/uploads/' or 'public/temp_uploads/'. Received: '{file_url_path}'")
        
        # Extract filename and determine directory
        if file_url_path.startswith("public/uploads/"):
            filename = file_url_path.replace("public/uploads/", "")
            directory = "uploads"
        else:  # public/temp_uploads/
            filename = file_url_path.replace("public/temp_uploads/", "")
            directory = "temp_uploads"
            
        logger.info(f"Extracted filename: '{filename}', directory: '{directory}'")
        
        if not filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # Delete file using file path
        deleted = file_handler.delete_file_by_path(file_url_path)
        
        if deleted:
            # Check if this file is the user's profile picture
            profile_photo = existing_user.get("profile_photo")
            logger.info(f"User ID: {user_id}")
            logger.info(f"User profile_photo: {profile_photo}")
            logger.info(f"File URL path to delete: {file_url_path}")
            
            if profile_photo:
                profile_uploadurl = profile_photo.get("uploadurl")
                profile_filename = profile_photo.get("uploadfilename")
                logger.info(f"Profile uploadurl: {profile_uploadurl}")
                logger.info(f"Profile filename: {profile_filename}")
                
                # Check for exact match or filename match
                url_match = profile_uploadurl == file_url_path
                filename_match = profile_filename and file_url_path.endswith(profile_filename)
                
                logger.info(f"URL match: {url_match}")
                logger.info(f"Filename match: {filename_match}")
                
                if url_match or filename_match:
                    # Remove profile_photo from database
                    result = await db.players.update_one(
                        {"_id": ObjectId(user_id)},
                        {
                            "$unset": {"profile_photo": ""},
                            "$set": {
                                "updated_on": datetime.utcnow(),
                                "updated_by": existing_user.get("username", "system")
                            }
                        }
                    )
                    
                    if result.modified_count > 0:
                        logger.info(f"Profile picture removed from database for user: {user_id}")
                    else:
                        logger.warning(f"Database update failed for user: {user_id}, modified_count: {result.modified_count}")
                else:
                    logger.info(f"File is not user's profile picture, skipping database update")
                    
                    # Also check if this file belongs to any other user
                    other_user = await db.players.find_one({
                        "profile_photo.uploadurl": file_url_path
                    })
                    if other_user:
                        logger.info(f"File belongs to another user: {other_user['_id']}")
                        # Remove from that user's profile
                        other_result = await db.players.update_one(
                            {"_id": other_user["_id"]},
                            {
                                "$unset": {"profile_photo": ""},
                                "$set": {
                                    "updated_on": datetime.utcnow(),
                                    "updated_by": existing_user.get("username", "system")
                                }
                            }
                        )
                        if other_result.modified_count > 0:
                            logger.info(f"Profile picture removed from other user: {other_user['_id']}")
            else:
                logger.info(f"User has no profile_photo, checking if file belongs to any user")
                # Check if this file belongs to any user
                other_user = await db.players.find_one({
                    "profile_photo.uploadurl": file_url_path
                })
                if other_user:
                    logger.info(f"File belongs to user: {other_user['_id']}")
                    # Remove from that user's profile
                    other_result = await db.players.update_one(
                        {"_id": other_user["_id"]},
                        {
                            "$unset": {"profile_photo": ""},
                            "$set": {
                                "updated_on": datetime.utcnow(),
                                "updated_by": existing_user.get("username", "system")
                            }
                        }
                    )
                    if other_result.modified_count > 0:
                        logger.info(f"Profile picture removed from user: {other_user['_id']}")
            
            logger.info(f"File deleted by user: {user_id}, file_url_path: {file_url_path}")
            return {"message": "File deleted successfully", "file_url_path": file_url_path}
        else:
            raise HTTPException(status_code=404, detail="File not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete file failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete file") 