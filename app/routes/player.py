from fastapi import APIRouter, HTTPException, Depends, Query, status, Body, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.player import PlayerUpdate, PlayerResponse, PlayerBalance, PlayerStats, TransactionResponse, PlayerCreate, PlayerStatusUpdate, PlayerListResponse
from app.models.player import Player
from app.auth.token_manager import token_manager
from app.services.analytics import analytics_service
from app.db.mongo import get_database
from app.utils.helpers import generate_unique_wallet_address
from app.common.prefix import generate_prefix
from app.common.profile_pic_upload.upload_handler import profile_pic_handler
import logging
from typing import List, Optional
from bson import ObjectId
from passlib.hash import bcrypt
from datetime import datetime
from fastapi.responses import Response
from pydantic import EmailStr

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

async def get_role_name(role_id, db):
    role = await db.roles.find_one({"_id": ObjectId(role_id)})
    return role["role"] if role else None

@router.get("/profile", response_model=PlayerResponse)
async def get_player_profile(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get player profile information."""
    try:
        # Verify token and get player
        payload = token_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid access token")
        
        player_id = payload.get("sub")
        db = get_database()
        
        # Get player
        player_doc = await db.players.find_one({"_id": player_id})
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
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update player profile information."""
    try:
        # Verify token and get player
        payload = token_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid access token")
        
        player_id = payload.get("sub")
        db = get_database()
        
        # Check if username is already taken
        if player_data.username:
            existing_player = await db.players.find_one({
                "username": player_data.username,
                "_id": {"$ne": player_id}
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
            await db.players.update_one({"_id": player_id}, {"$set": update_data})
        
        # Get updated player
        player_doc = await db.players.find_one({"_id": player_id})
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
async def get_player_balance(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get player token balance and transaction summary."""
    try:
        # Verify token and get player
        payload = token_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid access token")
        
        player_id = payload.get("sub")
        db = get_database()
        
        # Get player
        player_doc = await db.players.find_one({"_id": player_id})
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
async def get_player_stats(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get player gaming statistics."""
    try:
        # Verify token and get player
        payload = token_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid access token")
        
        player_id = payload.get("sub")
        
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
    credentials: HTTPAuthorizationCredentials = Depends(security),
    limit: int = 20,
    transaction_type: str = None
):
    """Get player transaction history."""
    try:
        # Verify token and get player
        payload = token_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid access token")
        
        player_id = payload.get("sub")
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
async def get_player_analytics(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get detailed player analytics."""
    try:
        # Verify token and get player
        payload = token_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid access token")
        
        player_id = payload.get("sub")
        
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

 