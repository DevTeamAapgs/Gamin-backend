from fastapi import APIRouter, HTTPException, Depends, Query, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.game import GameLevelUpdate, LeaderboardResponse
from app.schemas.player import AdminLogin, AdminCreate, AdminResponse, TokenResponse
from app.auth.token_manager import token_manager
from app.auth.cookie_auth import verify_admin, get_current_user
from app.utils.cookie_utils import set_auth_cookies, clear_auth_cookies
from app.services.analytics import analytics_service
from app.db.mongo import get_database
from app.services.logging_service import logging_service
from app.core.config import settings
from datetime import datetime, timedelta
import logging
from typing import Optional, List
from passlib.context import CryptContext
from bson import ObjectId

logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["admin"])
security = HTTPBearer()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    print(plain_password,hashed_password,"plain_password,hashed_password")
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

# Remove the old verify_admin function as we're importing it from cookie_auth

@router.post("/login", response_model=TokenResponse)
async def admin_login(admin_data: AdminLogin, response: Response):
    """Admin login with username and password."""
    try:
        print(admin_data.username,"username")
        db = get_database()
        
        # Find admin by username
        admin_doc = await db.players.find_one({
            "email": admin_data.username,
            "is_admin": True
        })
        
       
        if not admin_doc:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        print(get_password_hash(admin_data.password),"pwd")
        # Verify password
        if not verify_password(admin_data.password, admin_doc.get("password_hash", "")):
            print("invalid credentials")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if admin is active
        if not admin_doc.get("is_active", True):
            raise HTTPException(status_code=403, detail="Admin account is deactivated")
        
        # Update last login
        await db.players.update_one(
            {"_id": admin_doc["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Generate tokens
        access_token = token_manager.create_access_token({
            "sub": str(admin_doc["_id"]), 
            "username": admin_doc["username"],
            "is_admin": True
        })
        
        # Create refresh token
        refresh_token = token_manager.create_refresh_token({
            "sub": str(admin_doc["_id"]),
            "username": admin_doc["username"],
            "is_admin": True
        })
        
        logger.info(f"Admin logged in: {admin_doc['username']}")
        
        # Set cookies
        set_auth_cookies(response, access_token, refresh_token)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/create", response_model=AdminResponse)
async def create_admin(admin_data: AdminCreate, current_admin: dict = Depends(verify_admin)):
    """Create a new admin user (requires existing admin authentication)."""
    try:
        db = get_database()
        
        # Check if admin already exists
        existing_admin = await db.players.find_one({
            "username": admin_data.username,
            "is_admin": True
        })
        
        if existing_admin:
            raise HTTPException(status_code=400, detail="Admin already exists")
        
        # Create new admin
        admin_user = {
            "username": admin_data.username,
            "email": admin_data.email,
            "password_hash": get_password_hash(admin_data.password),
            "wallet_address": None,  # Placeholder
            "is_admin": True,
            "is_active": True,
            "is_verified": True,
            "token_balance": 0,
            "total_games_played": 0,
            "total_tokens_earned": 0,
            "total_tokens_spent": 0,
            "created_at": datetime.utcnow(),
            "last_login": None
        }
        
        result = await db.players.insert_one(admin_user)
        admin_user["_id"] = result.inserted_id
        
        logger.info(f"New admin created: {admin_data.username}")
        
        return AdminResponse(
            id=str(admin_user["_id"]),
            username=admin_user["username"],
            email=admin_user["email"],
            is_admin=admin_user["is_admin"],
            is_active=admin_user["is_active"],
            created_at=admin_user["created_at"],
            last_login=admin_user["last_login"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create admin failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create admin")

@router.get("/me", response_model=AdminResponse)
async def get_current_admin(current_admin: dict = Depends(verify_admin)):
    """Get current admin information."""
    try:
        db = get_database()
        admin_doc = await db.players.find_one({"_id": ObjectId(current_admin.get("sub"))})
        
        if not admin_doc or not admin_doc.get("is_admin"):
            raise HTTPException(status_code=404, detail="Admin not found")
        
        return AdminResponse(
            id=str(admin_doc["_id"]),
            username=admin_doc["username"],
            email=admin_doc.get("email"),
            is_admin=admin_doc["is_admin"],
            is_active=admin_doc.get("is_active", True),
            created_at=admin_doc["created_at"],
            last_login=admin_doc.get("last_login")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current admin failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get admin information")

@router.post("/refresh", response_model=TokenResponse)
async def admin_refresh_token(request: Request, response: Response):
    """Refresh admin access token using refresh token from cookies."""
    try:
        # Get refresh token from cookies
        from app.auth.cookie_auth import cookie_auth
        refresh_token = cookie_auth.get_refresh_token_from_cookies(request)
        
        if not refresh_token:
            raise HTTPException(status_code=401, detail="No refresh token found")
        
        # Verify refresh token
        payload = token_manager.verify_refresh_token(refresh_token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Check if it's an admin token
        if not payload.get("is_admin"):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        admin_id = payload.get("sub")
        username = payload.get("username")
        
        if not admin_id or not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Get admin from database
        db = get_database()
        admin_doc = await db.players.find_one({
            "_id": ObjectId(admin_id),
            "is_admin": True,
            "is_active": True
        })
        
        if not admin_doc:
            raise HTTPException(status_code=404, detail="Admin not found or inactive")
        
        # Generate new tokens
        access_token = token_manager.create_access_token({
            "sub": str(admin_doc["_id"]), 
            "username": admin_doc["username"],
            "is_admin": True
        })
        
        new_refresh_token = token_manager.create_refresh_token({
            "sub": str(admin_doc["_id"]),
            "username": admin_doc["username"],
            "is_admin": True
        })
        
        logger.info(f"Admin token refreshed: {admin_doc['username']}")
        
        # Set new cookies
        set_auth_cookies(response, access_token, new_refresh_token)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin token refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")

@router.post("/logout")
async def admin_logout(request: Request, response: Response):
    """Admin logout - clear authentication cookies."""
    try:
        # Clear authentication cookies
        clear_auth_cookies(response)
        
        logger.info("Admin logged out successfully")
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Admin logout failed: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

@router.get("/dashboard")
async def get_admin_dashboard(current_admin: dict = Depends(verify_admin)):
    """Get admin dashboard data."""
    try:
        # Get platform analytics
        platform_stats = await analytics_service.get_platform_analytics()
        
        return {
            "platform_stats": platform_stats,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get admin dashboard failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get admin dashboard")

@router.get("/analytics/platform")
async def get_platform_analytics(current_admin: dict = Depends(verify_admin)):
    """Get comprehensive platform analytics."""
    try:
        analytics = await analytics_service.get_platform_analytics()
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get platform analytics failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get platform analytics")

@router.get("/analytics/heatmap")
async def get_heatmap_data(
    game_type: str,
    level: int,
    time_range: str = "24h",
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get heatmap data for game interactions."""
    try:
        await verify_admin(credentials)
        
        heatmap_data = await analytics_service.generate_heatmap_data(game_type, level, time_range)
        
        return heatmap_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get heatmap data failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get heatmap data")

@router.put("/levels/{level_id}")
async def update_game_level(
    level_id: str,
    level_data: GameLevelUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update game level configuration."""
    try:
        await verify_admin(credentials)
        
        db = get_database()
        
        # Build update data
        update_data = {}
        if level_data.entry_cost is not None:
            update_data["entry_cost"] = level_data.entry_cost
        if level_data.reward_multiplier is not None:
            update_data["reward_multiplier"] = level_data.reward_multiplier
        if level_data.time_limit is not None:
            update_data["time_limit"] = level_data.time_limit
        if level_data.difficulty_multiplier is not None:
            update_data["difficulty_multiplier"] = level_data.difficulty_multiplier
        if level_data.max_attempts is not None:
            update_data["max_attempts"] = level_data.max_attempts
        if level_data.is_active is not None:
            update_data["is_active"] = level_data.is_active
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            result = await db.game_levels.update_one(
                {"_id": level_id},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                raise HTTPException(status_code=404, detail="Game level not found")
            
            logger.info(f"Game level {level_id} updated: {update_data}")
            
            return {"message": "Game level updated successfully"}
        else:
            return {"message": "No changes to update"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update game level failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to update game level")

@router.get("/players")
async def get_all_players(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    limit: int = 50,
    offset: int = 0,
    is_banned: bool = None
):
    """Get all players with optional filtering."""
    try:
        await verify_admin(credentials)
        
        db = get_database()
        
        # Build query
        query = {}
        if is_banned is not None:
            query["is_banned"] = is_banned
        
        # Get players
        players = await db.players.find(query).skip(offset).limit(limit).to_list(length=limit)
        total_count = await db.players.count_documents(query)
        
        return {
            "players": [
                {
                    "id": str(player["_id"]),
                    "username": player["username"],
                    "wallet_address": player["wallet_address"],
                    "email": player.get("email"),
                    "token_balance": player["token_balance"],
                    "total_games_played": player["total_games_played"],
                    "is_active": player["is_active"],
                    "is_banned": player["is_banned"],
                    "ban_reason": player.get("ban_reason"),
                    "created_at": player["created_at"],
                    "last_login": player.get("last_login")
                }
                for player in players
            ],
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get all players failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get players")

@router.post("/players/{player_id}/ban")
async def ban_player(
    player_id: str,
    reason: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Ban a player."""
    try:
        await verify_admin(credentials)
        
        db = get_database()
        
        result = await db.players.update_one(
            {"_id": player_id},
            {
                "$set": {
                    "is_banned": True,
                    "ban_reason": reason,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Player not found")
        
        logger.info(f"Player {player_id} banned: {reason}")
        
        return {"message": "Player banned successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ban player failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to ban player")

@router.post("/players/{player_id}/unban")
async def unban_player(
    player_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Unban a player."""
    try:
        await verify_admin(credentials)
        
        db = get_database()
        
        result = await db.players.update_one(
            {"_id": player_id},
            {
                "$set": {
                    "is_banned": False,
                    "ban_reason": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Player not found")
        
        logger.info(f"Player {player_id} unbanned")
        
        return {"message": "Player unbanned successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unban player failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to unban player")

@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    page: int = 1,
    page_size: int = 20
):
    """Get platform leaderboard."""
    try:
        await verify_admin(credentials)
        
        db = get_database()
        
        # Calculate skip
        skip = (page - 1) * page_size
        
        # Get players sorted by total tokens earned
        players = await db.players.find({}).sort("total_tokens_earned", -1).skip(skip).limit(page_size).to_list(length=page_size)
        total_players = await db.players.count_documents({})
        
        # Calculate ranks
        entries = []
        for i, player in enumerate(players):
            rank = skip + i + 1
            
            # Calculate win rate (simplified)
            win_rate = 0.5  # Placeholder - calculate from actual game data
            
            entries.append({
                "player_id": str(player["_id"]),
                "username": player["username"],
                "wallet_address": player["wallet_address"],
                "total_tokens_earned": player["total_tokens_earned"],
                "total_games_played": player["total_games_played"],
                "win_rate": win_rate,
                "average_completion": 75.0,  # Placeholder
                "rank": rank
            })
        
        return LeaderboardResponse(
            entries=entries,
            total_players=total_players,
            page=page,
            page_size=page_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get leaderboard failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get leaderboard")

@router.get("/transactions")
async def get_all_transactions(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    limit: int = 50,
    offset: int = 0,
    transaction_type: str = None
):
    """Get all transactions."""
    try:
        await verify_admin(credentials)
        
        db = get_database()
        
        # Build query
        query = {}
        if transaction_type:
            query["transaction_type"] = transaction_type
        
        # Get transactions
        transactions = await db.transactions.find(query).sort("created_at", -1).skip(offset).limit(limit).to_list(length=limit)
        total_count = await db.transactions.count_documents(query)
        
        return {
            "transactions": [
                {
                    "id": str(tx["_id"]),
                    "player_id": str(tx["player_id"]),
                    "transaction_type": tx["transaction_type"],
                    "amount": tx["amount"],
                    "game_id": str(tx["game_id"]) if tx.get("game_id") else None,
                    "description": tx["description"],
                    "status": tx["status"],
                    "tx_hash": tx.get("tx_hash"),
                    "created_at": tx["created_at"],
                    "completed_at": tx.get("completed_at")
                }
                for tx in transactions
            ],
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get all transactions failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get transactions")

@router.get("/logs/requests")
async def get_request_logs(
    player_id: Optional[str] = Query(None, description="Filter by player ID"),
    path: Optional[str] = Query(None, description="Filter by path"),
    status_code: Optional[int] = Query(None, description="Filter by status code"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(100, le=1000, description="Number of logs to return"),
    admin_token: dict = Depends(verify_admin)
):
    """Get request logs with filtering options."""
    try:
        logs = await logging_service.get_request_logs(
            player_id=player_id,
            path=path,
            status_code=status_code,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return {
            "success": True,
            "data": logs,
            "count": len(logs)
        }
    except Exception as e:
        logger.error(f"Failed to get request logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve request logs")

@router.get("/logs/security")
async def get_security_logs(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    player_id: Optional[str] = Query(None, description="Filter by player ID"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(100, le=1000, description="Number of logs to return"),
    admin_token: dict = Depends(verify_admin)
):
    """Get security logs with filtering options."""
    try:
        logs = await logging_service.get_security_logs(
            event_type=event_type,
            player_id=player_id,
            severity=severity,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return {
            "success": True,
            "data": logs,
            "count": len(logs)
        }
    except Exception as e:
        logger.error(f"Failed to get security logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve security logs")

@router.get("/logs/game-actions")
async def get_game_action_logs(
    game_id: Optional[str] = Query(None, description="Filter by game ID"),
    player_id: Optional[str] = Query(None, description="Filter by player ID"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(100, le=1000, description="Number of logs to return"),
    admin_token: dict = Depends(verify_admin)
):
    """Get game action logs with filtering options."""
    try:
        logs = await logging_service.get_game_action_logs(
            game_id=game_id,
            player_id=player_id,
            action_type=action_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return {
            "success": True,
            "data": logs,
            "count": len(logs)
        }
    except Exception as e:
        logger.error(f"Failed to get game action logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve game action logs")

@router.get("/logs/statistics")
async def get_log_statistics(
    admin_token: dict = Depends(verify_admin)
):
    """Get logging statistics and metrics."""
    try:
        stats = await logging_service.get_log_statistics()
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Failed to get log statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve log statistics")

@router.post("/logs/cleanup")
async def cleanup_old_logs(
    admin_token: dict = Depends(verify_admin)
):
    """Clean up old logs based on TTL."""
    try:
        result = await logging_service.cleanup_old_logs()
        
        return {
            "success": True,
            "data": result,
            "message": "Log cleanup completed successfully"
        }
    except Exception as e:
        logger.error(f"Failed to cleanup logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup logs")

@router.get("/logs/export")
async def export_logs(
    log_type: str = Query(..., description="Type of logs to export: requests, security, game-actions"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    format: str = Query("json", description="Export format: json, csv"),
    admin_token: dict = Depends(verify_admin)
):
    """Export logs in specified format."""
    try:
        if log_type == "requests":
            logs = await logging_service.get_request_logs(
                start_date=start_date,
                end_date=end_date,
                limit=10000  # Higher limit for export
            )
        elif log_type == "security":
            logs = await logging_service.get_security_logs(
                start_date=start_date,
                end_date=end_date,
                limit=10000
            )
        elif log_type == "game-actions":
            logs = await logging_service.get_game_action_logs(
                start_date=start_date,
                end_date=end_date,
                limit=10000
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid log type")
        
        if format == "csv":
            # Convert to CSV format
            import csv
            import io
            
            output = io.StringIO()
            if logs:
                writer = csv.DictWriter(output, fieldnames=logs[0].keys())
                writer.writeheader()
                writer.writerows(logs)
            
            return {
                "success": True,
                "data": output.getvalue(),
                "format": "csv",
                "filename": f"{log_type}_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        else:
            return {
                "success": True,
                "data": logs,
                "format": "json",
                "count": len(logs)
            }
            
    except Exception as e:
        logger.error(f"Failed to export logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to export logs") 