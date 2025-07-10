from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.player import PlayerCreate, PlayerLogin, PlayerResponse
from app.models.player import Player
from app.auth.token_manager import token_manager
from app.auth.cookie_auth import get_current_user, get_current_user_optional
from app.utils.cookie_utils import set_auth_cookies, clear_auth_cookies
from app.utils.upload_handler import profile_pic_handler
from app.utils.email_utils import email_manager
from app.db.mongo import get_database
from app.core.config import settings
from datetime import datetime
import logging
from app.models.schemas import TokenResponse, ForgotPasswordRequest, VerifyOTPRequest, ResetPasswordRequest
from pathlib import Path
from bson import ObjectId
from passlib.context import CryptContext

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

@router.post("/register", response_model=TokenResponse)
async def register_player(player_data: PlayerCreate, request: Request, response: Response):
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
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login", response_model=TokenResponse)
async def login_player(player_data: PlayerLogin, request: Request, response: Response):
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
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request, response: Response):
    """Refresh access token using refresh token from cookies."""
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
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")

@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout player and invalidate session."""
    try:
        # Get token from cookies or header
        from app.auth.cookie_auth import cookie_auth
        token = cookie_auth.get_token(request)
        
        if token:
            # Verify access token
            payload = token_manager.verify_token(token)
            if payload:
                player_id = payload.get("sub")
                if player_id:
                    # Invalidate session
                    token_hash = token_manager._generate_token_seed()  # Simplified for demo
                    await token_manager.invalidate_session(token_hash)
                    logger.info(f"Player logged out: {player_id}")
        
        # Clear cookies
        clear_auth_cookies(response)
        
        # Clean up temp files for this user
        if token:
            payload = token_manager.verify_token(token)
            if payload:
                player_id = payload.get("sub")
                if player_id:
                    await cleanup_user_temp_files_on_logout(player_id)
        
        return {"message": "Successfully logged out"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

@router.get("/me", response_model=PlayerResponse)
async def get_current_player(current_user: dict = Depends(get_current_user)):
    """Get current player information."""
    try:
        player_id = current_user.get("sub")
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

# Forgot Password Routes

@router.post("/forgot-password")
async def forgot_password(request_data: ForgotPasswordRequest):
    """Send OTP to email for password reset."""
    try:
        db = get_database()
        
        # Check if email exists in database
        user_doc = await db.players.find_one({"email": request_data.email})
        if not user_doc:
            raise HTTPException(status_code=404, detail="Email not found in our records")
        
        # Generate OTP
        otp = email_manager.generate_otp()
        otp_expiry = email_manager.get_otp_expiry_time()
        
        # Encrypt OTP and expiry time
        encrypted_otp = email_manager.encrypt_data(otp)
        encrypted_expiry = email_manager.encrypt_data(otp_expiry.isoformat())
        
        # Update user with encrypted OTP and expiry time
        await db.players.update_one(
            {"_id": user_doc["_id"]},
            {
                "$set": {
                    "otp": encrypted_otp,
                    "otp_expire_time": encrypted_expiry,
                    "updated_on": datetime.utcnow()
                }
            }
        )
        
        # Send OTP email
        username = user_doc.get("username", "User")
        email_sent = await email_manager.send_otp_email(request_data.email, username, otp)
        
        if not email_sent:
            raise HTTPException(status_code=500, detail="Failed to send OTP email")
        
        logger.info(f"OTP sent to {request_data.email} for user {user_doc['_id']}")
        
        return {"message": "OTP sent successfully to your email"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forgot password failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process forgot password request")

@router.post("/verify-otp")
async def verify_otp(request_data: VerifyOTPRequest):
    """Verify OTP and check if it's not expired."""
    try:
        db = get_database()
        
        # Find user by email
        user_doc = await db.players.find_one({"email": request_data.email})
        if not user_doc:
            raise HTTPException(status_code=404, detail="Email not found in our records")
        
        # Check if OTP exists
        if not user_doc.get("otp") or not user_doc.get("otp_expire_time"):
            raise HTTPException(status_code=400, detail="No OTP found. Please request a new OTP")
        
        # Decrypt OTP and expiry time
        try:
            stored_otp = email_manager.decrypt_data(user_doc["otp"])
            stored_expiry_str = email_manager.decrypt_data(user_doc["otp_expire_time"])
            stored_expiry = datetime.fromisoformat(stored_expiry_str)
        except Exception as e:
            logger.error(f"Failed to decrypt OTP data: {e}")
            raise HTTPException(status_code=500, detail="Invalid OTP data")
        
        # Check if OTP is expired
        if datetime.utcnow() > stored_expiry:
            # Clear OTP data
            await db.players.update_one(
                {"_id": user_doc["_id"]},
                {
                    "$unset": {"otp": "", "otp_expire_time": ""},
                    "$set": {"updated_on": datetime.utcnow()}
                }
            )
            raise HTTPException(status_code=400, detail="OTP expired")
        
        # Verify OTP
        if request_data.otp != stored_otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")
        
        # Clear OTP data after successful verification
        await db.players.update_one(
            {"_id": user_doc["_id"]},
            {
                "$unset": {"otp": "", "otp_expire_time": ""},
                "$set": {"updated_on": datetime.utcnow()}
            }
        )
        
        logger.info(f"OTP verified successfully for {request_data.email}")
        
        return {"message": "OTP verified successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OTP verification failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify OTP")

@router.post("/reset-password")
async def reset_password(request_data: ResetPasswordRequest):
    """Reset password after OTP verification."""
    try:
        db = get_database()
        
        # Find user by email
        user_doc = await db.players.find_one({"email": request_data.email})
        if not user_doc:
            raise HTTPException(status_code=404, detail="Email not found in our records")
        
        # Hash the new password
        hashed_password = get_password_hash(request_data.new_password)
        
        # Update password in database
        result = await db.players.update_one(
            {"_id": user_doc["_id"]},
            {
                "$set": {
                    "password_hash": hashed_password,
                    "updated_on": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to update password")
        
        logger.info(f"Password reset successfully for {request_data.email}")
        
        return {"message": "Password updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset password")

@router.get("/debug/email-config")
async def debug_email_config():
    """Debug endpoint to check email configuration (remove in production)"""
    try:
        from app.utils.email_utils import email_manager
        return {
            "username": email_manager.username,
            "server": email_manager.server,
            "port": email_manager.port,
            "tls": email_manager.tls,
            "ssl": email_manager.ssl,
            "from_email": email_manager.from_email,
            "password_set": "***" if email_manager.password else "NOT SET"
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/debug/otp/{email}")
async def debug_get_otp(email: str):
    """Debug endpoint to get OTP from database (remove in production)"""
    try:
        db = get_database()
        user_doc = await db.players.find_one({"email": email})
        if not user_doc:
            return {"error": "Email not found"}
        
        if not user_doc.get("otp") or not user_doc.get("otp_expire_time"):
            return {"error": "No OTP found for this email"}
        
        # Decrypt OTP and expiry time
        try:
            stored_otp = email_manager.decrypt_data(user_doc["otp"])
            stored_expiry_str = email_manager.decrypt_data(user_doc["otp_expire_time"])
            stored_expiry = datetime.fromisoformat(stored_expiry_str)
            
            return {
                "email": email,
                "otp": stored_otp,
                "expiry": stored_expiry.isoformat(),
                "is_expired": datetime.utcnow() > stored_expiry
            }
        except Exception as e:
            return {"error": f"Failed to decrypt OTP: {str(e)}"}
            
    except Exception as e:
        return {"error": str(e)}

