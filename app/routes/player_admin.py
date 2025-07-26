from fastapi import APIRouter, HTTPException, Depends, Query, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.enums import PlayerType
from app.db.mongo import get_database
from app.schemas.player import PlayerAdminGameAttemptListResponse, PlayerAdminGridListItem, PlayerAdminGridListResponse
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
from app.utils.crypto_utils import decrypt_player_fields, safe_float_decrypt
from app.schemas.game import GameResponse
from app.schemas.player import SessionWithUsernameListResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/grid-list", response_model=PlayerAdminGridListResponse)
async def player_admin_grid_list(
    params: dict = Depends(decrypt_data_param),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
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
                {"email": {"$regex": search, "$options": "i"}},
            ]
        if wallet_status is not None:
            # Accepts 'true'/'false' as string or bool
            if str(wallet_status).lower() == "true":
                query["wallet_address"] = {"$nin": [None, ""]}
            elif str(wallet_status).lower() == "false":
                query["$or"] = query.get("$or", []) + [
                    {"wallet_address": {"$in": [None, ""]}},
                    {"wallet_address": {"$exists": False}},
                ]
        skip = (page - 1) * count
        pipeline = [
            {"$match": query},
            {
                "$facet": {
                    "results": [
                        {"$sort": {"created_at": -1}},
                        {"$skip": skip},
                        {"$limit": count},
                        {
                            "$project": {
                                "_id": 0,
                                "id": {"$toString": "$_id"},
                                "username": 1,
                                "email": 1,
                                "wallet_status": {
                                    "$cond": [
                                        {"$ifNull": ["$wallet_address", False]},
                                        True,
                                        False,
                                    ]
                                },
                                "ip_address": "$ip_address",
                                "token_balance": 1,
                                "is_banned": 1,
                                "status": 1,
                            }
                        },
                    ],
                    "totalCount": [{"$count": "value"}],
                }
            },
        ]
        result = await db.players.aggregate(pipeline).to_list(length=1)
        if result:
            response_data = {
                "results": result[0]["results"],
                "total": (
                    result[0]["totalCount"][0]["value"]
                    if result[0]["totalCount"]
                    else 0
                ),
            }
        else:
            response_data = {"results": [], "total": 0}
        return PlayerAdminGridListResponse(**response_data)
    except Exception as e:
        logger.error(f"Player admin grid-list failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list players")


@router.post("/ban")
async def ban_player(
    request: Request,
    ban_data: BanPlayerRequest = Depends(decrypt_body(BanPlayerRequest)),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """Ban a player and record ban details. Payload must include player_id and reason."""
    try:
        current_user = current_user.model_dump()
        device_fingerprint = getattr(request.state, "device_fingerprint", None)
        client_ip = getattr(request.state, "client_ip", None)
        user_agent = getattr(request.state, "user_agent", None)
        player_id = ban_data.player_id
        player_obj_id = ObjectId(player_id)
        # Update Player document: only is_banned
        player_update = await db.players.update_one(
            {"_id": player_obj_id},
            {
                "$set": {
                    "is_banned": True,
                    "updated_on": datetime.utcnow(),
                    "updated_by": current_user.get("id"),
                }
            },
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
        banned_details["updated_by"] = current_user.get("id")
        banned_details["created_on"] = current_user.get("id")
        await db.player_banned_details.update_one(
            {"fk_player_id": player_obj_id}, {"$set": banned_details}, upsert=True
        )
        return {"message": "Player banned successfully"}
    except Exception as e:
        logger.error(f"Ban player failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to ban player")


@router.post("/unban")
async def unban_player(
    unban_data: UnbanPlayerRequest = Depends(decrypt_body(UnbanPlayerRequest)),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """Unban a player and update banned_until. Payload must include fk_player_id and banned_until."""
    try:
        current_user = current_user.model_dump()
        player_id = unban_data.fk_player_id
        # Update Player document: only is_banned
        player_update = await db.players.update_one(
            {"_id": ObjectId(player_id)},
            {
                "$set": {
                    "is_banned": False,
                    "updated_on": datetime.utcnow(),
                    "updated_by": current_user.get("id"),
                }
            },
        )
        if player_update.modified_count == 0:
            raise HTTPException(status_code=404, detail="Player not found")
        # Update only banned_until in PlayerBannedDetails, keep other defaults
        await db.player_banned_details.update_one(
            {"fk_player_id": ObjectId(player_id)},
            {
                "$set": {
                    "banned_status": False,
                    "banned_until": unban_data.banned_until,
                    "updated_on": datetime.utcnow(),
                    "updated_by": current_user.get("id"),
                }
            },
        )
        return {"message": "Player unbanned successfully"}
    except Exception as e:
        logger.error(f"Unban player failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to unban player")


@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player_by_id(
    player_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """Get a single player by player_id (path param) for admin panel."""
    try:
        player_doc = await db.players.find_one({"_id": ObjectId(player_id)})
        if not player_doc:
            raise HTTPException(status_code=404, detail="Player not found")
        player_doc = decrypt_player_fields(player_doc)
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
            last_login=player.last_login,
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get player by id failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get player")


@router.get("/{player_id}/game-attempts", response_model=PlayerAdminGameAttemptListResponse)
async def get_player_game_attempts(
    player_id: str,
    params: dict = Depends(decrypt_data_param),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """Get all game attempts for a player by player_id (admin), paginated, decrypted, with date filter and total count."""
    try:
        page = int(params.get("page", 1))
        limit = int(params.get("limit", 20))
        skip = (page - 1) * limit
        from_date = params.get("from_date")
        to_date = params.get("to_date")
        match_query = {"fk_player_id": ObjectId(player_id)}
        if from_date:
            from_dt = datetime.fromisoformat(from_date)
            from_dt = from_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            match_query["start_time"] = {"$gte": from_dt}
        if to_date:
            to_dt = datetime.fromisoformat(to_date)
            to_dt = to_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            if "start_time" in match_query:
                match_query["start_time"]["$lte"] = to_dt
            else:
                match_query["start_time"] = {"$lte": to_dt}
        pipeline = [
            {"$match": match_query},
            {
                "$facet": {
                    "results": [
                        {"$sort": {"created_on": -1}},
                        {"$skip": skip},
                        {"$limit": limit},
                        {
                            "$lookup": {
                                "from": "game_configuration",
                                "localField": "fk_game_configuration_id",
                                "foreignField": "_id",
                                "as": "game_configuration",
                            }
                        },
                        {
                            "$lookup": {
                                "from": "game_level_configuration",
                                "localField": "fk_game_level_id",
                                "foreignField": "_id",
                                "as": "game_level",
                            }
                        },
                        {
                            "$addFields": {
                                "game_type": {
                                    "$first": "$game_configuration.game_type"
                                },
                                "game_name": {
                                    "$first": "$game_configuration.game_name"
                                },
                                "level_name": {"$first": "$game_level.level_name"},
                                "level_number": {"$first": "$game_level.level_number"},
                                "level_type": {"$first": "$game_level.level_type"},
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "id": {"$toString": "$_id"},
                                "game_name": 1,
                                "level_name": 1,
                                "level_number": 1,
                                "level_type": 1,
                                "game_status": 1,
                                "score": 1,
                                "completion_percentage": 1,
                                "tokens_earned": 1,
                                "gems_earned": 1,
                                "entry_cost": 1,
                                "gems_spent": 1,
                                "start_time": 1,
                                "end_time": 1,
                                "duration": 1,
                                "moves_count": 1,
                                
                            }
                        },
                    ],
                    "totalCount": [{"$count": "value"}],
                }
            },
        ]
        facet_result = await db.game_attempt.aggregate(pipeline).to_list(length=1)
        if  len(facet_result[0]["results"]) == 0:
            return PlayerAdminGameAttemptListResponse(**{"results":[], "total":0})

        results = facet_result[0]["results"]
        total_count = facet_result[0]["totalCount"][0]["value"] if facet_result[0]["totalCount"] else 0
        return   PlayerAdminGameAttemptListResponse(**{"results":results, "total":total_count})
    except HTTPException as e:
        logger.error(f"Get game attempts for player failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Get game attempts for player failed: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get game attempts for player"
        )


@router.get("/{player_id}/sessions", response_model=SessionWithUsernameListResponse)
async def get_sessions_for_player(
    player_id: str,
    params: dict = Depends(decrypt_data_param),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all sessions for a specific player, including username, paginated, with optional last_activity date filter.
    """
    try:
        page = int(params.get("page", 1))
        limit = int(params.get("limit", 20))
        skip = (page - 1) * limit
        from_date = params.get("from_date")
        to_date = params.get("to_date")

        match_query = {"player_id": player_id}
        if from_date:
            from_dt = datetime.fromisoformat(from_date)
            from_dt = from_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            match_query["last_activity"] = {"$gte": from_dt}
        if to_date:
            to_dt = datetime.fromisoformat(to_date)
            to_dt = to_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            if "last_activity" in match_query:
                match_query["last_activity"]["$lte"] = to_dt
            else:
                match_query["last_activity"] = {"$lte": to_dt}

        pipeline = [
            {"$match": match_query},
            {"$project": {
                "_id": 0,
                "id": {"$toString": "$_id"},
                "device_fingerprint": 1,
                "ip_address": 1,
                "user_agent": 1,
                "expires_at": 1,
                "last_activity": 1
            }},
            {"$sort": {"last_activity": -1}},
            {"$skip": skip},
            {"$limit": limit}
        ]

        facet = [
            {"$facet": {
                "results": pipeline,
                "totalCount": [
                    {"$match": match_query},
                    {"$count": "value"}
                ]
            }}
        ]

        result = await db.sessions.aggregate(facet).to_list(length=1)
        results = result[0]["results"] if result else []
        total = result[0]["totalCount"][0]["value"] if result and result[0]["totalCount"] else 0

        return SessionWithUsernameListResponse(results=results, total=total)
    except Exception as e:
        logger.error(f"Get sessions for player failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sessions for player")


