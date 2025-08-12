from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId

from typing import  Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.enums import Status
from app.db.mongo import get_database
from app.auth.cookie_auth import verify_admin
from app.schemas.game_configuration_schema import GameConfigurationGridResponse, GameConfigurationSaveSchema
from app.utils.upload_handler import move_file_from_temp_to_uploads, unzip_and_move_to_game_dir
from passlib.context import CryptContext
from datetime import datetime
import logging
import traceback
from app.utils.crypto_dependencies import decrypt_body, decrypt_data_param
from app.models.game_configuration import GameConfigurationModel
from app.schemas.game_configuration_schema import GameConfigurationUpdateSchema, GameConfigurationStatusUpdateSchema, GameConfigurationResponse

logger = logging.getLogger(__name__)
router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 1. GET /admins - List all admins
@router.get("/grid-list", response_model=GameConfigurationGridResponse)
async def list_admins(
    params: dict = Depends(decrypt_data_param),
    current_admin: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    
    try:
        page = int(params.get("page", 1))
        count = int(params.get("count", 10))
        search_string = params.get("search_string")
        status = params.get("status")

        query: Dict[str, Any] = {}

        if search_string:
            query["$or"] = [
                {"game_name": {"$regex": search_string, "$options": "i"}},
            ]

        if status is not None:
            query["status"] = bool(status)

        skip = (page - 1) * count

        pipeline = [
            {"$match": query},
            {
                "$facet": {
                    "results": [
                        {"$sort": {"updated_on": -1}},
                        {"$skip": skip},
                        {"$limit": count},
                        {
                            "$project": {
                            "_id": 0,
                            "id": "$_id",
                            "game_name": 1,
                            "game_icon": 1,
                            "game_description": 1,
                            "game_type_name": 1,
                            "status": 1,
                        }
                        }
                    ],
                    "totalCount": [
                        {"$count": "value"}
                    ]
                }
            }
        ]

        result = await db.game_configuration.aggregate(pipeline).to_list(length=1)
        print(result[0]["results"])
        if result:
            response_data = {
                "results": result[0]["results"],
                "total": result[0]["totalCount"][0]["value"] if result[0]["totalCount"] else 0
            }
        else:
            response_data = {"results": [], "total": 0}

        return GameConfigurationGridResponse(**response_data)

    except Exception as e:
        logger.error(f"List admins failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list admins")


# 2. POST /admins - Create user
@router.post("")
async def create_game_configuration(
    game_configuration_data: GameConfigurationSaveSchema = Depends(decrypt_body(GameConfigurationSaveSchema)),
    current_admin: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        
        role_doc = await db.game_configuration.find_one({"game_name": game_configuration_data.game_name})
        if  role_doc:
            raise HTTPException(status_code=400, detail=f"Game name '{game_configuration_data.game_name}' already exists")

        game_icon = move_file_from_temp_to_uploads(game_configuration_data.game_icon)
        
        game_banner = []
        if game_configuration_data.game_banner:
            for banner in game_configuration_data.game_banner:
                game_banner.append(move_file_from_temp_to_uploads(banner))
        
        # Handle game assets (zip file)
        game_assets = None
        if game_configuration_data.game_assets:
            try:
                game_assets = unzip_and_move_to_game_dir(
                    game_configuration_data.game_assets, 
                    game_name=game_configuration_data.game_name
                )
            except Exception as e:
                logger.error(f"Failed to process game assets: {e}")
                raise HTTPException(status_code=400, detail=f"Failed to process game assets: {str(e)}")
        
        # Create user document
        user_doc = {
            "game_name": game_configuration_data.game_name,
            "game_icon": game_icon,
            "game_banner": game_banner,
            "game_description": game_configuration_data.game_description,
            "game_type_name": game_configuration_data.game_type_name,
            "game_assets": game_assets,
            "created_by": current_admin.get("_id"),
            "updated_by": current_admin.get("_id"),
        }
        
        game_configuration_model = GameConfigurationModel(**user_doc)
        result = await db.game_configuration.insert_one(game_configuration_model.model_dump())

        user_doc["_id"] = result.inserted_id
        
        return {"message": "Game created successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create admin failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create admin: {str(e)}")


# 3. PUT /game-configuration - Update game configuration
@router.put("")
async def update_game_configuration(
    game_configuration_data: GameConfigurationUpdateSchema = Depends(decrypt_body(GameConfigurationUpdateSchema)),
    current_admin: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        # Check if the game exists
        game_id = game_configuration_data.id
        existing_game = await db.game_configuration.find_one({"_id": ObjectId(game_id)})
        if not existing_game:
            raise HTTPException(status_code=404, detail="Game configuration not found")

        # Check for duplicate game name (excluding current)
        duplicate = await db.game_configuration.find_one({
            "game_name": game_configuration_data.game_name,
            "_id": {"$ne": ObjectId(game_id)}
        })
        if duplicate:
            raise HTTPException(status_code=400, detail=f"Game name '{game_configuration_data.game_name}' already exists")

        # Handle file moves for icon and banner
        game_icon = move_file_from_temp_to_uploads(game_configuration_data.game_icon)
        game_banner = []
        if game_configuration_data.game_banner:
            for banner in game_configuration_data.game_banner:
                game_banner.append(move_file_from_temp_to_uploads(banner))

        # Handle game assets (zip file)
        game_assets = None
        if game_configuration_data.game_assets:
            try:
                game_assets = unzip_and_move_to_game_dir(
                    game_configuration_data.game_assets, 
                    game_name=game_configuration_data.game_name
                )
            except Exception as e:
                logger.error(f"Failed to process game assets: {e}")
                raise HTTPException(status_code=400, detail=f"Failed to process game assets: {str(e)}")

        update_doc = {
            "game_name": game_configuration_data.game_name,
            "game_icon": game_icon,
            "game_banner": game_banner,
            "game_description": game_configuration_data.game_description,
            "game_type_name": game_configuration_data.game_type_name,
            "updated_by": current_admin.get("_id"),
            "updated_on": datetime.utcnow(),
        }

        # Only add game_assets to update if it was provided
        if game_assets is not None:
            update_doc["game_assets"] = game_assets

        result = await db.game_configuration.update_one(
            {"_id": ObjectId(game_id)},
            {"$set": update_doc}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No changes made to the game configuration")

        return {"message": "Game configuration updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update game configuration failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to update game configuration: {str(e)}")


# 4. GET /game-configuration/{game_id} - Get game configuration by id
@router.get("/{game_id}", response_model=GameConfigurationResponse)
async def get_game_configuration(
    game_id: str,
    current_admin: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        game = await db.game_configuration.find_one(
            {"_id": ObjectId(game_id)}, 
            projection={
                "_id": 0, 
                "id": "$_id", 
                "game_name": 1,  
                "game_description": 1, 
                "game_type_name": 1,
                "game_banner": 1, 
                "game_icon": 1, 
                "game_assets": 1,
                "status": 1
            }
        )
        if not game:
            raise HTTPException(status_code=404, detail="Game configuration not found")
        return GameConfigurationResponse(**game).model_dump(by_alias=True)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get game configuration failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get game configuration: {str(e)}")

# 5. PATCH /game-configuration/status - Update status only
@router.patch("/status")
async def update_game_configuration_status(
    status_update: GameConfigurationStatusUpdateSchema = Depends(decrypt_body(GameConfigurationStatusUpdateSchema)),
    current_admin: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        game_id = status_update.id
        result = await db.game_configuration.update_one(
            {"_id": ObjectId(game_id)},
            {"$set": {"status": status_update.status, "updated_by": current_admin.get("_id"), "updated_on": datetime.utcnow()}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Game configuration not found")
        return {"message": "Game configuration status updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update game configuration status failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to update game configuration status: {str(e)}")

# 6. DELETE /game-configuration/{game_id} - Delete game configuration
@router.delete("/{game_id}")
async def delete_game_configuration(
    game_id: str,
    current_admin: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        result = await db.game_configuration.delete_one({"_id": ObjectId(game_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Game configuration not found")
        return {"message": "Game configuration deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete game configuration failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to delete game configuration: {str(e)}")






