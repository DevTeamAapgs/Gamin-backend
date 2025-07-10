from fastapi import APIRouter, HTTPException, Depends, Query, status, Body, UploadFile, File, Form, Request
from app.schemas.player import PlayerUpdate, PlayerResponse, PlayerBalance, PlayerStats, TransactionResponse, PlayerCreate, PlayerStatusUpdate, PlayerListResponse
from app.models.player import Player
from app.auth.cookie_auth import get_current_user
from app.services.analytics import analytics_service
from app.db.mongo import get_database
from app.utils.helpers import generate_unique_wallet_address
from app.utils.prefix import generate_prefix
from app.utils.upload_handler import profile_pic_handler
import logging
from typing import List, Optional
from bson import ObjectId
from passlib.hash import bcrypt
from datetime import datetime
from fastapi.responses import Response
from pydantic import EmailStr
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_role_name(role_id, db):
    role = await db.roles.find_one({"_id": ObjectId(role_id)})
    return role["role_name"] if role else None

async def get_role_id_for_mapping(role_name, db):
    """Map role names to the 'Sample by sivas' role ID for admin, manager, player"""
    role_name_lower = role_name.lower()
    
    # For admin, manager, player - map to "Sample by sivas" role
    if role_name_lower in ["admin", "manager", "player"]:
        sample_role = await db.roles.find_one({"role_name": "Sample by sivas"})
        if sample_role:
            return sample_role["_id"]
        else:
            raise HTTPException(status_code=400, detail="Role 'Sample by sivas' not found")
    
    # For other roles, look up by role_name
    role_doc = await db.roles.find_one({"role_name": role_name})
    if role_doc:
        return role_doc["_id"]
    else:
        raise HTTPException(status_code=400, detail=f"Role '{role_name}' not found")

@router.get("/profile", response_model=PlayerResponse)
async def get_player_profile(current_user: Player = Depends(get_current_user)):
    """Get player profile information."""
    try:
        db = get_database()
        
        # Get player
        player_doc = await db.players.find_one({"_id": ObjectId(str(current_user.id))})
        if not player_doc:
            raise HTTPException(status_code=404, detail="Player not found")
        
        player_doc["id"] = str(player_doc["_id"])
        player_doc["fk_role_id"] = str(player_doc["fk_role_id"])
        player_doc["role"] = await get_role_name(player_doc["fk_role_id"], db)
        
        return PlayerResponse(**player_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get player profile failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get player profile")

@router.put("/profile", response_model=PlayerResponse)
async def update_player_profile(
    player_data: PlayerUpdate,
    current_user: Player = Depends(get_current_user)
):
    """Update player profile information."""
    try:
        db = get_database()
        player_id = str(current_user.id)
        
        # Check if username is already taken
        if player_data.username:
            existing_player = await db.players.find_one({
                "username": player_data.username,
                "_id": {"$ne": ObjectId(player_id)}
            })
            if existing_player:
                raise HTTPException(status_code=400, detail="Username already taken")
        
        # Update player
        update_data = {}
        if player_data.username:
            update_data["username"] = player_data.username
        if player_data.email:
            update_data["email"] = player_data.email
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            await db.players.update_one({"_id": ObjectId(player_id)}, {"$set": update_data})
        
        # Get updated player
        player_doc = await db.players.find_one({"_id": ObjectId(player_id)})
        player_doc["id"] = str(player_doc["_id"])
        player_doc["fk_role_id"] = str(player_doc["fk_role_id"])
        player_doc["role"] = await get_role_name(player_doc["fk_role_id"], db)
        
        return PlayerResponse(**player_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update player profile failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to update player profile")

@router.get("/balance", response_model=PlayerBalance)
async def get_player_balance(current_user: Player = Depends(get_current_user)):
    """Get player token balance and transaction summary."""
    try:
        db = get_database()
        
        # Get player
        player_doc = await db.players.find_one({"_id": ObjectId(str(current_user.id))})
        if not player_doc:
            raise HTTPException(status_code=404, detail="Player not found")
        
        return PlayerBalance(
            token_balance=player_doc.get("token_balance", 0),
            total_earned=player_doc.get("total_tokens_earned", 0),
            total_spent=player_doc.get("total_tokens_spent", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get player balance failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get player balance")

@router.get("/stats", response_model=PlayerStats)
async def get_player_stats(current_user: Player = Depends(get_current_user)):
    """Get player gaming statistics."""
    try:
        player_id = str(current_user.id)
        
        # Get analytics data
        analytics = await analytics_service.get_player_analytics(player_id)
        
        if "error" in analytics:
            raise HTTPException(status_code=404, detail=analytics["error"])
        
        # Calculate additional stats
        total_games = analytics["total_games"]
        completed_games = analytics["completed_games"]
        games_lost = total_games - completed_games
        win_rate = analytics["completion_rate"]
        avg_completion = analytics["average_completion"]
        total_earned = analytics.get("total_tokens_earned", 0)
        total_spent = analytics.get("total_tokens_spent", 0)
        net_profit = total_earned - total_spent
        
        return PlayerStats(
            total_games_played=total_games,
            games_won=completed_games,
            games_lost=games_lost,
            win_rate=win_rate,
            average_completion=avg_completion,
            total_tokens_earned=total_earned,
            total_tokens_spent=total_spent,
            net_profit=net_profit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get player stats failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get player stats")

@router.get("/transactions", response_model=list[TransactionResponse])
async def get_player_transactions(
    current_user: Player = Depends(get_current_user),
    limit: int = 20,
    transaction_type: str = None
):
    """Get player transaction history."""
    try:
        player_id = str(current_user.id)
        db = get_database()
        
        # Build query
        query = {"player_id": player_id}
        if transaction_type:
            query["transaction_type"] = transaction_type
        
        # Get transactions
        transactions = await db.transactions.find(query).sort("created_at", -1).limit(limit).to_list(length=limit)
        
        return [
            TransactionResponse(
                id=str(tx["_id"]),
                player_id=str(tx["player_id"]),
                transaction_type=tx["transaction_type"],
                amount=tx["amount"],
                game_id=str(tx["game_id"]) if tx.get("game_id") else None,
                description=tx["description"],
                status=tx["status"],
                tx_hash=tx.get("tx_hash"),
                created_at=tx["created_at"],
                completed_at=tx.get("completed_at")
            )
            for tx in transactions
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get player transactions failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get player transactions")

@router.get("/analytics")
async def get_player_analytics(current_user: Player = Depends(get_current_user)):
    """Get detailed player analytics."""
    try:
        player_id = str(current_user.id)
        
        # Get analytics data
        analytics = await analytics_service.get_player_analytics(player_id)
        
        if "error" in analytics:
            raise HTTPException(status_code=404, detail=analytics["error"])
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get player analytics failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get player analytics")

 