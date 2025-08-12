from fastapi import APIRouter, HTTPException, Depends, Request, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.game import GameStart, GameSubmit, GameResponse, GameLevelResponse
from app.models.game import GameAttempt, GameReplay
from app.models.player import Player
from app.auth.token_manager import token_manager
from app.auth.cookie_auth import get_current_user
from app.services.game_engine import game_engine
from app.services.analytics import analytics_service
from app.db.mongo import get_database
from datetime import datetime
import logging
from typing import Callable, Annotated

from app.utils.crypto_dependencies import decrypt_body

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

@router.post("/start", response_model=GameResponse)
async def start_game(
    request: Request, 
    game_data: GameStart = Depends(decrypt_body(GameStart)), 
    current_user: dict = Depends(get_current_user)
):
    """Start a new game."""
    try:
        # Get player from current user
        player_id = current_user.get("sub")
        if not player_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        db = get_database()
        
        # Get player
        player_doc = await db.players.find_one({"_id": player_id})
        if not player_doc:
            raise HTTPException(status_code=404, detail="Player not found")
        
        player = Player(**player_doc)
        
        # Check if player has enough tokens
        level_config = await db.game_levels.find_one({"level_number": game_data.level, "game_type": game_data.game_type})
        if not level_config:
            raise HTTPException(status_code=404, detail="Game level not found")
        
        entry_cost = level_config.get("entry_cost", 100)
        if player.token_balance < entry_cost:
            raise HTTPException(status_code=400, detail="Insufficient token balance")
        
        # Calculate adaptive difficulty
        difficulty = await game_engine.calculate_adaptive_difficulty(
            str(player.id), game_data.game_type, game_data.level, 1
        )
        
        # Generate game state
        game_state = await game_engine.generate_game_state(
            game_data.game_type, game_data.level, difficulty
        )
        
        # Create game
        game = GameAttempt(
            player_id=player.id,
            game_type=game_data.game_type,
            level=game_data.level,
            entry_cost=entry_cost,
            reward_multiplier=level_config.get("reward_multiplier", 1.0),
            time_limit=level_config.get("time_limit", 60),
            game_state=game_state
        )
        
        # Save game to database
        result = await db.games.insert_one(game.dict(by_alias=True))
        game.id = result.inserted_id
        
        # Deduct tokens from player
        await db.players.update_one(
            {"_id": player.id},
            {
                "$inc": {
                    "token_balance": -entry_cost,
                    "total_tokens_spent": entry_cost
                }
            }
        )
        
        # Create transaction record
        transaction = {
            "player_id": player.id,
            "transaction_type": "game_entry",
            "amount": entry_cost,
            "game_id": game.id,
            "description": f"Game entry cost for {game_data.game_type} level {game_data.level}",
            "status": "completed",
            "created_at": datetime.utcnow()
        }
        await db.transactions.insert_one(transaction)
        
        logger.info(f"Game started: {game_data.game_type} level {game_data.level} by {player.username}")
        
        response = GameResponse(
            id=str(game.id),
            player_id=str(game.player_id),
            game_type=game.game_type,
            level=game.level,
            status=game.status,
            entry_cost=game.entry_cost,
            reward_multiplier=game.reward_multiplier,
            time_limit=game.time_limit,
            completion_percentage=game.completion_percentage,
            final_reward=game.final_reward,
            start_time=game.start_time,
            end_time=game.end_time,
            created_at=game.created_at
        )
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Start game failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to start game")

@router.post("/submit")
async def submit_game(
    request: Request, 
    game_data: GameSubmit = Depends(decrypt_body(GameSubmit)), 
    current_user: dict = Depends(get_current_user)
):
    """Submit game completion."""
    try:
        # Get player from current user
        player_id = current_user.get("sub")
        if not player_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        db = get_database()
        
        # Get game
        game_doc = await db.games.find_one({"_id": game_data.game_id})
        if not game_doc:
            raise HTTPException(status_code=404, detail="Game not found")
        
        game = GameAttempt(**game_doc)
        
        # Verify game belongs to player
        if str(game.fk_player_id) != player_id:
            raise HTTPException(status_code=403, detail="Game does not belong to player")
        
        # Validate game completion
        validation_result = await game_engine.validate_game_completion(
            game_data.game_id, game_data.dict()
        )
        
        if validation_result["cheat_detected"]:
            # Handle cheating
            await db.players.update_one(
                {"_id": game.fk_player_id},
                {"$set": {"is_banned": True, "ban_reason": validation_result["cheat_reason"]}}
            )
            raise HTTPException(status_code=403, detail="Cheating detected")
        
        completion_percentage = validation_result["completion_percentage"]
        
        # Calculate reward
        reward = await game_engine.calculate_reward(
            completion_percentage, game.entry_cost, game.reward_multiplier
        )
        
        # Update game
        game_update = {
            "status": "completed" if completion_percentage >= 80 else "failed",
            "completion_percentage": completion_percentage,
            "final_reward": reward,
            "end_time": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.games.update_one({"_id": game.id}, {"$set": game_update})
        
        # Update player stats and balance
        player_update = {
            "$inc": {
                "total_games_played": 1,
                "total_tokens_earned": reward,
                "token_balance": reward
            }
        }
        await db.players.update_one({"_id": game.fk_player_id}, player_update)
        
        # Create transaction for reward
        if reward > 0:
            reward_transaction = {
                "player_id": game.fk_player_id,
                "transaction_type": "reward",
                "amount": reward,
                "game_id": game.id,
                "description": f"Game reward for {completion_percentage}% completion",
                "status": "completed",
                "created_at": datetime.utcnow()
            }
            await db.transactions.insert_one(reward_transaction)
        
        # Save replay data
        replay = GameReplay(
            game_id=game.id,
            fk_player_id=game.fk_player_id,
            replay_data=game_data.dict(),
            action_sequence=game_data.actions,
            mouse_movements=game_data.mouse_movements,
            click_positions=game_data.click_positions,
            timing_data=game_data.timing_data,
            device_info=game_data.device_info,
            ip_address="unknown"
        )
        await db.replays.insert_one(replay.dict(by_alias=True))
        
        # Track analytics
        await analytics_service.track_game_action(
            str(game.id), str(game.fk_player_id), {
                "type": "game_completion",
                "completion_percentage": completion_percentage,
                "reward": reward,
                "success": completion_percentage >= 80
            }
        )
        
        logger.info(f"Game submitted: {completion_percentage}% completion, {reward} tokens earned")
        
        response_data = {
            "game_id": str(game.id),
            "completion_percentage": completion_percentage,
            "reward": reward,
            "status": game_update["status"]
        }
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Submit game failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit game")

@router.get("/levels", response_model=list[GameLevelResponse])
async def get_game_levels(request: Request, game_type: str = "color_match"):
    """Get available game levels."""
    try:
        db = get_database()
        
        levels = await db.game_levels.find({"game_type": game_type, "is_active": True}).to_list(length=100)
        
        response_data = [
            GameLevelResponse(
                id=str(level["_id"]),
                level_number=level["level_number"],
                game_type=level["game_type"],
                name=level["name"],
                description=level["description"],
                entry_cost=level["entry_cost"],
                reward_multiplier=level["reward_multiplier"],
                time_limit=level["time_limit"],
                difficulty_multiplier=level["difficulty_multiplier"],
                max_attempts=level["max_attempts"],
                is_active=level["is_active"]
            )
            for level in levels
        ]
        return response_data
        
    except Exception as e:
        logger.error(f"Get game levels failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get game levels")

@router.get("/history")
async def get_game_history(request: Request, current_user: dict = Depends(get_current_user), limit: int = 10):
    """Get player's game history."""
    try:
        player_id = current_user.get("sub")
        if not player_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        db = get_database()
        
        # Get player's games
        games = await db.games.find({"fk_player_id": player_id}).sort("created_at", -1).limit(limit).to_list(length=limit)
        
        response_data = [
            {
                "id": str(game["_id"]),
                "game_type": game["game_type"],
                "level": game["level"],
                "status": game["status"],
                "completion_percentage": game.get("completion_percentage", 0),
                "final_reward": game.get("final_reward", 0),
                "start_time": game["start_time"],
                "end_time": game.get("end_time"),
                "created_at": game["created_at"]
            }
            for game in games
        ]
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get game history failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get game history")

@router.get("/leaderboard")
async def get_game_leaderboard(request: Request, game_type: str = "color_match", level: int = 1, limit: int = 20):
    """Get leaderboard for specific game type and level."""
    try:
        db = get_database()
        
        # Get top players for this game type and level
        pipeline = [
            {"$match": {"game_type": game_type, "level": level, "status": "completed"}},
            {"$group": {
                "_id": "$fk_player_id",
                "best_completion": {"$max": "$completion_percentage"},
                "total_games": {"$sum": 1},
                "total_reward": {"$sum": "$final_reward"}
            }},
            {"$sort": {"best_completion": -1}},
            {"$limit": limit},
            {"$lookup": {
                "from": "players",
                "localField": "_id",
                "foreignField": "_id",
                "as": "player"
            }},
            {"$unwind": "$player"}
        ]
        
        leaderboard = await db.games.aggregate(pipeline).to_list(length=limit)
        
        response_data = [
            {
                "rank": i + 1,
                "player_id": str(entry["_id"]),
                "username": entry["player"]["username"],
                "wallet_address": entry["player"]["wallet_address"],
                "best_completion": entry["best_completion"],
                "total_games": entry["total_games"],
                "total_reward": entry["total_reward"]
            }
            for i, entry in enumerate(leaderboard)
        ]
        return response_data
        
    except Exception as e:
        logger.error(f"Get game leaderboard failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get game leaderboard") 