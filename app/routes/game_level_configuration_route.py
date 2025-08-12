from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.mongo import get_database
from app.auth.cookie_auth import verify_admin
from app.schemas.game_Level_configuration_schema import (
    GameLevelConfigurationGridResponse,
    GameLevelConfigurationSaveSchema,
    GameLevelConfigurationUpdateSchema,
    GameLevelConfigurationResponse,
    GameLevelConfigurationStatusUpdateSchema
)
from app.utils.crypto_dependencies import decrypt_body, decrypt_data_param
from app.models.game_configuration import GameLevelConfigurationModel
from datetime import datetime
import logging
import traceback

logger = logging.getLogger(__name__)
router = APIRouter()

# 1. GET /game-level/grid-list
@router.get("/grid-list", response_model=GameLevelConfigurationGridResponse)
async def list_game_levels(
    params: dict = Depends(decrypt_data_param),
    current_admin: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        page = int(params.get("page", 1))
        count = int(params.get("count", 10))
        fk_game_configuration_id = params.get("fk_game_configuration_id")
        search_string = params.get("search_string")
        status = params.get("status")

        if not fk_game_configuration_id:
            raise HTTPException(status_code=400, detail="fk_game_configuration_id is required")

        query: Dict[str, Any] = {"fk_game_configuration_id": ObjectId(fk_game_configuration_id)}

        if search_string:
            query["$or"] = [
                {"level_name": {"$regex": search_string, "$options": "i"}},
                {"description": {"$regex": search_string, "$options": "i"}},
            ]
        if status is not None:
            query["status"] = status

        skip = (page - 1) * count

        pipeline = [
            {"$match": query},
            {"$facet": {
                "results": [
                    {"$sort": {"created_on": -1}},
                    {"$skip": skip},
                    {"$limit": count},
                    {"$project": {
                        "_id": 0,
                        "id": "$_id",
                        "level_name": 1,
                        "level_number": 1,
                        "description": 1,
                        "fk_game_configuration_id": 1,
                        "entry_cost": 1,
                        "reward_coins": 1,
                        "time_limit": 1,
                        "max_attempts": 1,
                        "add_details": 1,
                        "status": 1,
                    }}
                ],
                "totalCount": [
                    {"$count": "value"}
                ]
            }}
        ]

        result = await db.game_level_configuration.aggregate(pipeline).to_list(length=1)

        if result:
            response_data = {
                "results": result[0]["results"],
                "total": result[0]["totalCount"][0]["value"] if result[0]["totalCount"] else 0
            }
        else:
            response_data = {"results": [], "total": 0}

        return GameLevelConfigurationGridResponse(**response_data)
    except Exception as e:
        logger.error(f"List game levels failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list game levels")

# 2. POST /game-level
@router.post("")
async def create_game_level_configuration(
    level_data: GameLevelConfigurationSaveSchema = Depends(decrypt_body(GameLevelConfigurationSaveSchema)),
    current_admin: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        # Check for duplicate level number in the same game
        duplicate = await db.game_level_configuration.find_one({
            "fk_game_configuration_id": ObjectId(level_data.fk_game_configuration_id),
            "level_number": level_data.level_number
        })
        if duplicate:
            raise HTTPException(status_code=400, detail=f"Level number '{level_data.level_number}' already exists for this game")

        doc = level_data.dict()
        doc["fk_game_configuration_id"] = ObjectId(doc["fk_game_configuration_id"])
        doc["created_by"] = current_admin.get("_id")
        doc["updated_by"] = current_admin.get("_id")
        doc["created_on"] = datetime.utcnow()
        doc["updated_on"] = datetime.utcnow()
        model = GameLevelConfigurationModel(**doc)
        result = await db.game_level_configuration.insert_one(model.model_dump())
        return {"message": "Game level created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create game level failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create game level: {str(e)}")

# 3. PUT /game-level
@router.put("")
async def update_game_level_configuration(
    level_data: GameLevelConfigurationUpdateSchema = Depends(decrypt_body(GameLevelConfigurationUpdateSchema)),
    current_admin: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        level_id = level_data.id
        existing = await db.game_level_configuration.find_one({"_id": ObjectId(level_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Game level configuration not found")
        # Check for duplicate level number in the same game (excluding current)
        duplicate = await db.game_level_configuration.find_one({
            "fk_game_configuration_id": ObjectId(level_data.fk_game_configuration_id),
            "level_number": level_data.level_number,
            "_id": {"$ne": ObjectId(level_id)}
        })
        if duplicate:
            raise HTTPException(status_code=400, detail=f"Level number '{level_data.level_number}' already exists for this game")
        update_doc = level_data.dict(exclude={"id"})
        update_doc["fk_game_configuration_id"] = ObjectId(update_doc["fk_game_configuration_id"])
        update_doc["updated_by"] = current_admin.get("_id")
        update_doc["updated_on"] = datetime.utcnow()
        result = await db.game_level_configuration.update_one(
            {"_id": ObjectId(level_id)},
            {"$set": update_doc}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No changes made to the game level configuration")
        return {"message": "Game level configuration updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update game level configuration failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to update game level configuration: {str(e)}")

# 4. GET /game-level/{level_id}
@router.get("/{level_id}", response_model=GameLevelConfigurationResponse)
async def get_game_level_configuration(
    level_id: str,
    current_admin: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        print(level_id,"level_id")
        level = await db.game_level_configuration.find_one({"_id": ObjectId(level_id)}, projection={"_id": 0, "id": "$_id", "level_name": 1, "level_number": 1, "description": 1, "fk_game_configuration_id": 1, "entry_cost": 1, "reward_coins": 1, "time_limit": 1, "max_attempts": 1, "add_details": 1, "status": 1})
        if not level:
            raise HTTPException(status_code=404, detail="Game level configuration not found")
        return GameLevelConfigurationResponse(**level).model_dump(by_alias=True)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get game level configuration failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get game level configuration: {str(e)}")

# 5. PATCH /game-level/status
@router.patch("/status")
async def update_game_level_configuration_status(
    status_update: GameLevelConfigurationStatusUpdateSchema = Depends(decrypt_body(GameLevelConfigurationStatusUpdateSchema)),
    current_admin: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        level_id = status_update.id
        result = await db.game_level_configuration.update_one(
            {"_id": ObjectId(level_id)},
            {"$set": {"status": status_update.status, "updated_by": current_admin.get("_id"), "updated_on": datetime.utcnow()}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Game level configuration not found")
        return {"message": "Game level configuration status updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update game level configuration status failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to update game level configuration status: {str(e)}")

# 6. DELETE /game-level/{level_id}
@router.delete("/{level_id}")
async def delete_game_level_configuration(
    level_id: str,
    current_admin: dict = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        result = await db.game_level_configuration.delete_one({"_id": ObjectId(level_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Game level configuration not found")
        return {"message": "Game level configuration deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete game level configuration failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to delete game level configuration: {str(e)}") 