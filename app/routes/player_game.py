from fastapi import APIRouter, HTTPException, Depends, Request, Query
from app.schemas.player_game import GameListResponse, GameListItem, GameDetailItem, GameLevelItem
from app.auth.cookie_auth import get_current_user
from app.db.mongo import get_database
from app.core.enums import PlayerType, Status
from app.utils.crypto_dependencies import decrypt_data_param, decrypt_query
from bson import ObjectId
import logging
from typing import Optional
from datetime import datetime
import math

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/list", response_model=GameListResponse)
async def list_games(
    request: Request,
    current_user: dict = Depends(get_current_user),
    
    params: dict = Depends(decrypt_data_param),
):
    """
    List all games with pagination for players.
    Only accessible by players (PLAYER = 2).
    """
    try:
        page = int(params.get("page", 1))
        page_size = int(params.get("count", 10))
        status = params.get("status")
        game_type = params.get("game_type")

        # Check if user is a player
        if current_user.player_type != PlayerType.PLAYER:
            raise HTTPException(
                status_code=403, 
                detail="Access denied. Only players can access this endpoint."
            )
        
        db = get_database()
        
        # Build filter query
        filter_query = {}
        
        if game_type:
            filter_query["game_type_name"] = game_type
            
        if status is not None:
            filter_query["status"] = status
        
        # Get total count for pagination
        total_count = await db.game_configuration.count_documents(filter_query)
        
        
        skip = (page - 1) * page_size
        
        # Get games with pagination
        games_cursor = db.game_configuration.find(filter_query).skip(skip).limit(page_size)
        games = await games_cursor.to_list(length=page_size)
        
        # Convert to response format
        game_list = []
        for game in games:
            game_item = GameListItem(
                id=str(game["_id"]),
                game_name=game["game_name"],
                game_description=game.get("game_description", ""),
                game_type_name=game["game_type_name"],
                game_banner=game.get("game_banner", []),
                game_icon=game.get("game_icon", {}),
                game_assets=game.get("game_assets"),
                status=game.get("status", Status.ACTIVE),
                created_at=game.get("created_at", datetime.utcnow()),
                updated_at=game.get("updated_at")
            )
            game_list.append(game_item)
        
        # Build response
        response = GameListResponse(
            games=game_list,
            total_count=total_count,
            page=page,
            page_size=page_size,
        )
        
        logger.info(f"Player {current_user.username} listed games. Page: {page}, Total: {total_count}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List games failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list games")

@router.get("/{game_id}", response_model=GameDetailItem)
async def get_game_details(
    request: Request,
    game_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed information about a specific game including all levels.
    Only accessible by players (PLAYER = 2).
    """
    try:
        # Check if user is a player
        if current_user.player_type != PlayerType.PLAYER:
            raise HTTPException(
                status_code=403, 
                detail="Access denied. Only players can access this endpoint."
            )
        
        db = get_database()
        
        # Get game details
        try:
            game_object_id = ObjectId(game_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid game ID format")
            
        game = await db.game_configuration.find_one({"_id": game_object_id})
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Get all levels for this game
        levels_cursor = db.game_level_configuration.find({"fk_game_configuration_id": game_object_id})
        levels = await levels_cursor.to_list(length=100)
        
        # Convert levels to response format
        level_list = []
        for level in levels:
            level_item = GameLevelItem(
                id=str(level["_id"]),
                level_name=level["level_name"],
                level_number=level["level_number"],
                description=level["description"],
                entry_cost=level["entry_cost"],
                reward_coins=level.get("reward_coins", 0),
                level_type=level["level_type"],
                entry_cost_gems=level.get("entry_cost_gems", {}),
                reward_gems=level.get("reward_gems", {}),
                time_limit=level["time_limit"],
                max_attempts=level.get("max_attempts", 3),
                add_details=level.get("add_details", []),
                status=level.get("status", Status.ACTIVE),
                created_at=level.get("created_at", datetime.utcnow()),
                updated_at=level.get("updated_at")
            )
            level_list.append(level_item)
        
        # Convert to response format with levels
        game_item = GameDetailItem(
            id=str(game["_id"]),
            game_name=game["game_name"],
            game_description=game.get("game_description", ""),
            game_type_name=game["game_type_name"],
            game_banner=game.get("game_banner", []),
            game_icon=game.get("game_icon", {}),
            game_assets=game.get("game_assets"),
            status=game.get("status", Status.ACTIVE),
            created_at=game.get("created_at", datetime.utcnow()),
            updated_at=game.get("updated_at"),
            levels=level_list
        )
        
        logger.info(f"Player {current_user.username} viewed game details with {len(level_list)} levels: {game_id}")
        
        return game_item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get game details failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get game details") 