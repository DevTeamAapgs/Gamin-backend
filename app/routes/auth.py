from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.player import PlayerCreate, PlayerLogin, TokenResponse, PlayerResponse
from app.models.player import Player
from app.auth.token_manager import token_manager
from app.db.mongo import get_database
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

@router.post("/register", response_model=TokenResponse)
async def register_player(player_data: PlayerCreate, request: Request):
    """Register a new player."""
    try:
        db = get_database()
        
        # Check if player already exists
        existing_player = await db.players.find_one({
            "$or": [
                {"wallet_address": player_data.wallet_address},
                {"username": player_data.username}
            ]
        })
        
        if existing_player:
            raise HTTPException(status_code=400, detail="Player already exists")
        
        # Create new player
        player = Player(
            wallet_address=player_data.wallet_address,
            username=player_data.username,
            email=player_data.email,
            device_fingerprint=player_data.device_fingerprint,
            ip_address=request.client.host if request.client else "unknown"
        )
        
        # Save to database
        result = await db.players.insert_one(player.dict(by_alias=True))
        player.id = result.inserted_id
        
        # Create session and tokens
        device_fingerprint = player_data.device_fingerprint or "default"
        session = await token_manager.create_player_session(
            player, device_fingerprint, request.client.host if request.client else "unknown"
        )
        
        # Generate tokens
        access_token = token_manager.create_access_token({"sub": str(player.id), "wallet": player.wallet_address})
        refresh_token = session.refresh_token
        
        logger.info(f"New player registered: {player.username}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login", response_model=TokenResponse)
async def login_player(player_data: PlayerLogin, request: Request):
    """Login existing player."""
    try:
        db = get_database()
        
        # Find player by wallet address
        player_doc = await db.players.find_one({"wallet_address": player_data.wallet_address})
        if not player_doc:
            raise HTTPException(status_code=404, detail="Player not found")
        
        player = Player(**player_doc)
        
        # Check if player is banned
        if player.is_banned:
            raise HTTPException(status_code=403, detail="Account is banned")
        
        # Update last login and IP
        await db.players.update_one(
            {"_id": player.id},
            {
                "$set": {
                    "last_login": datetime.utcnow(),
                    "ip_address": request.client.host if request.client else "unknown",
                    "device_fingerprint": player_data.device_fingerprint
                }
            }
        )
        
        # Create new session
        session = await token_manager.create_player_session(
            player, player_data.device_fingerprint, player_data.ip_address
        )
        
        # Generate tokens
        access_token = token_manager.create_access_token({"sub": str(player.id), "wallet": player.wallet_address})
        refresh_token = session.refresh_token
        
        logger.info(f"Player logged in: {player.username}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, request: Request):
    """Refresh access token using refresh token."""
    try:
        # Verify refresh token
        payload = token_manager.verify_refresh_token(refresh_token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        player_id = payload.get("sub")
        if not player_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Get player
        db = get_database()
        player_doc = await db.players.find_one({"_id": player_id})
        if not player_doc:
            raise HTTPException(status_code=404, detail="Player not found")
        
        player = Player(**player_doc)
        
        # Check if player is banned
        if player.is_banned:
            raise HTTPException(status_code=403, detail="Account is banned")
        
        # Generate new tokens
        access_token = token_manager.create_access_token({"sub": str(player.id), "wallet": player.wallet_address})
        new_refresh_token = token_manager.create_refresh_token({"sub": str(player.id), "wallet": player.wallet_address})
        
        # Update session
        await db.sessions.update_one(
            {"refresh_token": refresh_token},
            {"$set": {"refresh_token": new_refresh_token}}
        )
        
        logger.info(f"Token refreshed for player: {player.username}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security), request: Request = None):
    """Logout player and invalidate session."""
    try:
        # Verify access token
        payload = token_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid access token")
        
        player_id = payload.get("sub")
        if not player_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Invalidate session
        token_hash = token_manager._generate_token_seed()  # Simplified for demo
        await token_manager.invalidate_session(token_hash)
        
        logger.info(f"Player logged out: {player_id}")
        
        return {"message": "Successfully logged out"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

@router.get("/me", response_model=PlayerResponse)
async def get_current_player(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current player information."""
    try:
        # Verify access token
        payload = token_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid access token")
        
        player_id = payload.get("sub")
        if not player_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Get player
        db = get_database()
        player_doc = await db.players.find_one({"_id": player_id})
        if not player_doc:
            raise HTTPException(status_code=404, detail="Player not found")
        
        player = Player(**player_doc)
        
        return PlayerResponse(
            id=str(player.id),
            wallet_address=player.wallet_address,
            username=player.username,
            email=player.email,
            token_balance=player.token_balance,
            total_games_played=player.total_games_played,
            total_tokens_earned=player.total_tokens_earned,
            total_tokens_spent=player.total_tokens_spent,
            is_active=player.is_active,
            created_at=player.created_at,
            last_login=player.last_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current player failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get player information") 