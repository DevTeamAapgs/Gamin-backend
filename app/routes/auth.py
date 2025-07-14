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
from datetime import datetime, timedelta
import logging
from app.models.adminschemas import TokenResponse, ForgotPasswordRequest, VerifyOTPRequest, ResetPasswordRequest
from pathlib import Path
from bson import ObjectId
from passlib.context import CryptContext
from jose import jwt, JWTError
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

@router.post("/register", response_model=TokenResponse)
async def register_player(player_data: PlayerCreate, request: Request, response: Response, db: AsyncIOMotorDatabase = Depends(get_database) ):
    """Register a new player."""
    try:
        
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
async def login_player(player_data: PlayerLogin, request: Request, response: Response, db: AsyncIOMotorDatabase = Depends(get_database)):
    """Login existing player."""
    try:
        
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
async def refresh_token(request: Request, response: Response, db: AsyncIOMotorDatabase = Depends(get_database)):
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
        player_doc = await db.players.find_one({"_id": player_id})
        if not player_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
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
async def logout(request: Request, response: Response, db: AsyncIOMotorDatabase = Depends(get_database)):
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
async def get_current_player(current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_database)):
    """Get current player information."""
    try:
        player_id = current_user.get("sub")
        if not player_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Get player
        player_doc = await db.players.find_one({"_id": player_id})
        if not player_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
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
async def forgot_password(request_data: ForgotPasswordRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    """Send OTP to email for password reset."""
    try:
        
        # Check if email exists in database
        user_doc = await db.players.find_one({"email": request_data.email})
        if not user_doc:
            raise HTTPException(status_code=404, detail="Invalid Email Address")
        
        # Generate OTP
        otp = email_manager.generate_otp()
        otp_expiry = email_manager.get_otp_expiry()
        
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
        email_sent = await email_manager.send_otp_email(request_data.email, user_doc.get("username", "User"), otp)
        
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
async def verify_otp(request_data: VerifyOTPRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    """Verify OTP and check if it's not expired. If valid, generate a reset token."""
    try:
        user_doc = await db.players.find_one({"email": request_data.email})
        if not user_doc:
            raise HTTPException(status_code=404, detail="Invalid Email Address")
        if not user_doc.get("otp") or not user_doc.get("otp_expire_time"):
            raise HTTPException(status_code=400, detail=" OTP Expired. Please request a new OTP")
        try:
            stored_otp = email_manager.decrypt_data(user_doc["otp"])
            stored_expiry_str = email_manager.decrypt_data(user_doc["otp_expire_time"])
            stored_expiry = datetime.fromisoformat(stored_expiry_str)
        except Exception as e:
            logger.error(f"Failed to decrypt OTP data: {e}")
            raise HTTPException(status_code=500, detail="Invalid OTP data")
        if datetime.utcnow() > stored_expiry:
            await db.players.update_one(
                {"_id": user_doc["_id"]},
                {"$unset": {"otp": "", "otp_expire_time": ""}, "$set": {"updated_on": datetime.utcnow()}}
            )
            raise HTTPException(status_code=400, detail="OTP expired")
        if request_data.otp != stored_otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")
        # Clear OTP data after successful verification
        await db.players.update_one(
            {"_id": user_doc["_id"]},
            {"$unset": {"otp": "", "otp_expire_time": ""}, "$set": {"updated_on": datetime.utcnow()}}
        )
        # Generate reset token (JWT, 15 min expiry)
        reset_token_expiry = datetime.utcnow() + timedelta(minutes=15)
        reset_token = jwt.encode(
            {"sub": str(user_doc["_id"]), "email": user_doc["email"], "exp": reset_token_expiry},
            settings.secret_key,
            algorithm=settings.algorithm
        )
        await db.players.update_one(
            {"_id": user_doc["_id"]},
            {"$set": {"reset_token": reset_token, "reset_token_expiry": reset_token_expiry}}
        )
        logger.info(f"OTP verified and reset token generated for {request_data.email}")
        return {"message": "OTP verified successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OTP verification failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify OTP")

@router.post("/reset-password")
async def reset_password(request_data: ResetPasswordRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    """Reset password using a secure reset token."""
    try:
        user_doc = await db.players.find_one({"email": request_data.email})
        if not user_doc:
            raise HTTPException(status_code=404, detail="Invalid ceredentials")
        stored_token = user_doc.get("reset_token")
        stored_expiry = user_doc.get("reset_token_expiry")
        if not stored_token or not stored_expiry:
            raise HTTPException(status_code=400, detail="Invalid ceredentials. Please request a new password reset.")
        if stored_token != request_data.reset_token:
            raise HTTPException(status_code=400, detail="Invalid ceredentials.")
        try:
            payload = jwt.decode(request_data.reset_token, settings.secret_key, algorithms=[settings.algorithm])
            if datetime.utcnow() > stored_expiry:
                raise HTTPException(status_code=400, detail="Reset token expired.")
        except JWTError:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token.")
        # Prevent using the previous password
        if verify_password(request_data.new_password, user_doc.get("password_hash", "")):
            raise HTTPException(status_code=400, detail="New password cannot be the same as the previous password.")
        hashed_password = get_password_hash(request_data.new_password)
        result = await db.players.update_one(
            {"_id": user_doc["_id"]},
            {"$set": {"password_hash": hashed_password, "updated_on": datetime.utcnow()}, "$unset": {"reset_token": "", "reset_token_expiry": ""}}
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




