from fastapi import APIRouter, HTTPException, Depends, Query, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.enums import PlayerType
from app.db.mongo import get_database
from app.schemas.player import PlayerAdminGridListItem, PlayerAdminGridListResponse
from app.auth.cookie_auth import get_current_user
from app.schemas.player_ban_schema import BanPlayerRequest, UnbanPlayerRequest
from bson import ObjectId
import logging
from app.utils.crypto_dependencies import decrypt_data_param, decrypt_body
from app.models.player_banned_details import PlayerBannedDetails
from datetime import datetime, timedelta
from typing import Optional
from app.models.player import Player
from app.schemas.player import PlayerResponse

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

@router.post("/ban")
async def ban_player(
    request: Request,
    ban_data: BanPlayerRequest = Depends(decrypt_body(BanPlayerRequest)),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Ban a player and record ban details. Payload must include player_id and reason."""
    try:
        current_user = current_user.model_dump()
        device_fingerprint = getattr(request.state, 'device_fingerprint', None)
        client_ip = getattr(request.state, 'client_ip', None)
        user_agent = getattr(request.state, 'user_agent', None)
        player_id = ban_data.player_id
        player_obj_id = ObjectId(player_id)
        # Update Player document: only is_banned
        player_update = await db.players.update_one(
            {"_id": player_obj_id},
            {"$set": {"is_banned": True, "updated_on": datetime.utcnow(), "updated_by": current_user.get('id')}}
        )
        if player_update.modified_count == 0:
            raise HTTPException(status_code=404, detail="Player not found")
        # Upsert PlayerBannedDetails with defaults from model
        banned_details = PlayerBannedDetails(
            fk_player_id=player_obj_id,
            reason=ban_data.reason,
            banned_status=True,
            banned_until=None,
            banned_by_name=current_user.get("username"),
            banned_by_ip=client_ip,
            banned_by_device_fingerprint=device_fingerprint,
        ).model_dump(exclude_none=True)
        banned_details["updated_on"] = datetime.utcnow()
        banned_details["updated_by"] = current_user.get('id')
        banned_details["created_on"] = current_user.get('id')
        await db.player_banned_details.update_one(
            {"fk_player_id": player_obj_id},
            {"$set": banned_details},
            upsert=True
        )
        return {"message": "Player banned successfully"}
    except Exception as e:
        logger.error(f"Ban player failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to ban player")

@router.post("/unban")
async def unban_player(
    unban_data: UnbanPlayerRequest = Depends(decrypt_body(UnbanPlayerRequest)),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Unban a player and update banned_until. Payload must include fk_player_id and banned_until."""
    try:
        current_user = current_user.model_dump()
        player_id = unban_data.fk_player_id
        # Update Player document: only is_banned
        player_update = await db.players.update_one(
            {"_id": ObjectId(player_id)},
            {"$set": {"is_banned": False, "updated_on": datetime.utcnow(), "updated_by": current_user.get('id')}}
        )
        if player_update.modified_count == 0:
            raise HTTPException(status_code=404, detail="Player not found")
        # Update only banned_until in PlayerBannedDetails, keep other defaults
        await db.player_banned_details.update_one(
            {"fk_player_id": ObjectId(player_id)},
            {"$set": {"banned_status": False, "banned_until": unban_data.banned_until, "updated_on": datetime.utcnow(), "updated_by": current_user.get('id')}}
        )
        return {"message": "Player unbanned successfully"}
    except Exception as e:
        logger.error(f"Unban player failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to unban player")

@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player_by_id(
    player_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Get a single player by player_id (path param) for admin panel."""
    try:
        player_doc = await db.players.find_one({"_id": ObjectId(player_id)})
        if not player_doc:
            raise HTTPException(status_code=404, detail="Player not found")
        player = Player(**player_doc)
        response = PlayerResponse(
            id=str(player_doc.get("_id")),
            wallet_address=player.wallet_address,
            player_prefix=getattr(player, "player_prefix", None),
            profile_photo=getattr(player, "profile_photo", None),
            player_type=getattr(player, "player_type", None),
            is_verified=getattr(player, "is_verified", None),
            token_balance=player.token_balance,
            total_games_played=player.total_games_played,
            total_tokens_earned=player.total_tokens_earned,
            username=player.username,
            email=player.email,
            last_login=player.last_login
            
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get player by id failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get player") 
