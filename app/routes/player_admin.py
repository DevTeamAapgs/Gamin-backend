from fastapi import APIRouter, HTTPException, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.enums import PlayerType
from app.db.mongo import get_database
from app.schemas.player import PlayerAdminGridListItem, PlayerAdminGridListResponse
from app.auth.cookie_auth import get_current_user
from pydantic import BaseModel
from bson import ObjectId
import logging
from app.utils.crypto_dependencies import decrypt_data_param

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/grid-list", response_model=PlayerAdminGridListResponse)
async def player_admin_grid_list(
    params: dict = Depends(decrypt_data_param),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    try:
        page = int(params.get("page", 1))
        count = int(params.get("count", 10))
        search = params.get("search_string")
        wallet_status = params.get("wallet_status")
        query = {"player_type": PlayerType.PLAYER}
        if search:
            query["$or"] = [
                {"username": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}}
            ]
        if wallet_status is not None:
            # Accepts 'true'/'false' as string or bool
            if str(wallet_status).lower() == 'true':
                query["wallet_address"] = {"$nin": [None, ""]}
            elif str(wallet_status).lower() == 'false':
                query["$or"] = query.get("$or", []) + [
                    {"wallet_address": {"$in": [None, ""]}},
                    {"wallet_address": {"$exists": False}}
                ]
        skip = (page - 1) * count
        pipeline = [
            {"$match": query},
            {"$facet": {
                "results": [
                    {"$sort": {"created_at": -1}},
                    {"$skip": skip},
                    {"$limit": count},
                    {"$project": {
                        "_id": 0,
                        "id": {"$toString": "$_id"},
                        "username": 1,
                        "email": 1,
                        "wallet_status": {"$cond": [{"$ifNull": ["$wallet_address", False]}, True, False]},
                        "ip_address": "$ip_address",
                        "token_balance": 1,
                        "is_banned": 1,
                        "status": 1
                    }}
                ],
                "totalCount": [
                    {"$count": "value"}
                ]
            }}
        ]
        result = await db.players.aggregate(pipeline).to_list(length=1)
        if result:
            response_data = {
                "results": result[0]["results"],
                "pagination": result[0]["totalCount"][0]["value"] if result[0]["totalCount"] else 0
            }
        else:
            response_data = {"results": [], "pagination": 0}
        return PlayerAdminGridListResponse(**response_data)
    except Exception as e:
        logger.error(f"Player admin grid-list failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list players") 
