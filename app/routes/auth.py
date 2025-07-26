from contextlib import asynccontextmanager
from re import A
from fastapi.responses import JSONResponse
from traceback import print_tb
from fastapi import APIRouter, Body, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Any,Optional
from app.schemas.player import AdminLogin, PlayerCreate, PlayerLogin, PlayerResponse
from app.models.player import Player, PlayerCreation,PlayerResponse
from app.auth.token_manager import token_manager
from app.auth.cookie_auth import get_current_user, get_current_user_optional
from app.utils.cookie_utils import set_auth_cookies, clear_auth_cookies
from app.utils.crypto_utils import encrypt_player_fields
from app.utils.crypto import AESCipher
from app.utils.crypto_dependencies import get_crypto_service
from app.utils.prefix import generate_prefix
from app.utils.upload_handler import profile_pic_handler
from app.utils.email_utils import email_manager
from app.db.mongo import get_database
from app.core.config import settings
from datetime import datetime, timedelta
from app.schemas.player import PlayerInfoSchema
import logging
from app.db.mongo import get_database
from app.auth.cookie_auth import get_current_user
from typing import Annotated, Callable
import os
import json
from app.models.game import GemType
import shutil
from pathlib import Path
from app.core.enums import PlayerType,MailType

from app.utils.crypto_dependencies import decrypt_body
from app.schemas.admin_curd_schemas import TokenResponse
from app.schemas.admin_curd_schemas import ForgotPasswordRequest, VerifyOTPRequest, ResetPasswordRequest
from pathlib import Path
from bson import ObjectId
from passlib.context import CryptContext
from jose import jwt, JWTError
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.player import CustomPlayerResponse, MenuItem, PermissionItem

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def cleanup_user_temp_files_on_logout(player_id: str):
    """Clean up temporary files for a user on logout."""
    try:
        temp_dir = Path("public/temp_uploads")
        if not temp_dir.exists():
            return
        
        # Find and delete temp files for this user
        for file_path in temp_dir.glob(f"*_{player_id}_*"):
            try:
                file_path.unlink()
                logger.info(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete temp file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Cleanup failed for user {player_id}: {e}")

@router.post("/register")
async def request_registration_otp(
    player_data: PlayerCreate = Depends(decrypt_body(PlayerCreate)),
    db: AsyncIOMotorDatabase = Depends(get_database),crypto: AESCipher = Depends(get_crypto_service)
):
    try:
        # Check if player already exists
        existing_player = await db.players.find_one({
            "$or": [{"username": player_data.username}, {"email": player_data.email}]
        })
        if existing_player:
            raise HTTPException(status_code=400, detail="Player already exists")

        # Generate OTP
        otp = email_manager.generate_otp()
        otp_expiry = email_manager.get_otp_expiry()

        encrypted_otp = email_manager.encrypt_data(otp)
        encrypted_expiry = email_manager.encrypt_data(otp_expiry.isoformat())
        print("token_balance",crypto.encrypt(str(1000)))
        print("gems",crypto.encrypt(str(50)))
        print("gems",crypto.encrypt(str(50)))
        print("gems",crypto.encrypt(str(50)))

        # Store OTP and user info in temporary collection
        await db.new_players.update_one(
            {"email": player_data.email},
            {
                "$set": {
                    "username": player_data.username,
                    "email": player_data.email,
                    "otp": encrypted_otp,
                    "otp_expire_time": encrypted_expiry,
                    "updated_on": datetime.utcnow(),
                }
            },
            upsert=True
        )
       
        # Send email
        email_sent = await email_manager.send_otp_email(
            player_data.email, player_data.username, otp,MailType.PLAYERREGISTER.value
        )
        if not email_sent:
            raise HTTPException(status_code=500, detail="Failed to send OTP email")

        return {"message": "OTP sent to your email. Please verify to complete registration."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Request OTP failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to send OTP")

@router.post("/register/verify", response_model=TokenResponse)
async def verify_otp_and_register(
    request: Request,
    response: Response,
    player_data: PlayerCreate = Depends(decrypt_body(PlayerCreate)),
    db: AsyncIOMotorDatabase = Depends(get_database),
    crypto: AESCipher = Depends(get_crypto_service),
):
    try:
        device_fingerprint = getattr(request.state, 'device_fingerprint', None)
        client_ip = getattr(request.state, 'client_ip', None)
        user_agent = getattr(request.state, 'user_agent', None)
        temp_user = await db.new_players.find_one({"email": player_data.email})
        if not temp_user:
            raise HTTPException(status_code=404, detail="OTP not found or expired")

        stored_otp = email_manager.decrypt_data(temp_user["otp"])
        otp_expiry_str = email_manager.decrypt_data(temp_user["otp_expire_time"])
        otp_expiry = datetime.fromisoformat(otp_expiry_str)
        print("stored otp",stored_otp)
        print("player_data.otp",player_data.otp)
        if player_data.otp != stored_otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")
        if datetime.utcnow() > otp_expiry:
            raise HTTPException(status_code=400, detail="OTP has expired")

        # OTP is valid → Register player
        player_prefix = await generate_prefix("player", 4, db=db)
        player_id = ObjectId()

        player = PlayerCreation(
            id=player_id,
            username=player_data.username,
            email=player_data.email,
            password_hash=get_password_hash(player_data.password),
            device_fingerprint=device_fingerprint,
            ip_address=client_ip,
            player_prefix=player_prefix,
            player_type=PlayerType.PLAYER,
            is_banned=False,
            ban_reason=None,
            is_active=True,
            status=1,
            fk_role_id=None,
            created_on=datetime.utcnow(),
            updated_on=datetime.utcnow(),
            created_by=None,
            wallet_address=None,
            token_balance=0,
            total_games_played=0,
            total_tokens_earned=0,
            total_tokens_spent=0,
            last_login=None,
            profile_photo=None
        )

        # Convert model to dict
        player_dict = player.model_dump(exclude_none=True)
        print("player_dict",player_dict)
        print("token_balance",crypto.encrypt(str(1000)))
        print("gems",crypto.encrypt(str(50)))
        print("gems",crypto.encrypt(str(50)))
        print("gems",crypto.encrypt(str(50)))
        
        ENCRYPTED_FIELDS = [
            "token_balance", "total_tokens_earned", "total_tokens_spent",
            "gems.blue", "gems.red", "gems.green"
        ]
        for field in ENCRYPTED_FIELDS:
            keys = field.split(".")
            if len(keys) == 1:
                key = keys[0]
                if key in player_dict and player_dict[key] is not None:
                    player_dict[key] = crypto.encrypt(str(player_dict[key]))
            elif len(keys) == 2:
                outer, inner = keys
                if outer in player_dict and isinstance(player_dict[outer], dict):
                    if inner in player_dict[outer] and player_dict[outer][inner] is not None:
                        player_dict[outer][inner] = crypto.encrypt(str(player_dict[outer][inner]))
        # Encrypt required fields before saving
        encrypted_fields = player_dict

        # Insert encrypted player into DB
        await db.players.insert_one(encrypted_fields)

        # Clean up temp user
        await db.new_players.delete_one({"_id": temp_user["_id"]}) 

        session = await token_manager.create_player_session(
            {"id": str(player_id), **player.model_dump()},
            device_fingerprint or "unknown",
            client_ip or "unknown",
            user_agent or "unknown"
        )

        access_token = token_manager.create_access_token({"sub": str(player_id), "wallet": player.wallet_address})
        refresh_token = session.refresh_token
        set_auth_cookies(response, access_token, refresh_token)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OTP verification failed: {e}")
        raise HTTPException(status_code=500, detail="OTP verification failed")

@router.post("/login", response_model=TokenResponse)
async def login_player(request: Request, response: Response, player_data: AdminLogin = Depends(decrypt_body(AdminLogin)), db:AsyncIOMotorDatabase = Depends(get_database)):
    """Login existing player."""
    try:
        # Access request details set by SecurityLoggingMiddleware
        device_fingerprint = getattr(request.state, 'device_fingerprint', None)
        client_ip = getattr(request.state, 'client_ip', None)
        user_agent = getattr(request.state, 'user_agent', None)
        
        # Find player by wallet address
        player_doc = await db.players.find_one({"email": player_data.username , "player_type":PlayerType.PLAYER})
        if not player_doc:
            raise HTTPException(status_code=404, detail="Player not found")

        crypto = get_crypto_service()
        # Decrypt numeric fields
        for field in ["token_balance", "total_tokens_earned", "total_tokens_spent"]:
            value = player_doc.get(field, "0")
            if isinstance(value, str):
                try:
                    player_doc[field] = float(crypto.decrypt(value))
                except Exception:
                    player_doc[field] = 0.0
            else:
                player_doc[field] = float(value)

        # Decrypt gems
        gems_value = player_doc.get("gems", {})
        if isinstance(gems_value, dict):
            decrypted_gems = {}
            for color in ["blue", "green", "red"]:
                val = gems_value.get(color, "0")
                if isinstance(val, str):
                    try:
                        decrypted_gems[color] = int(crypto.decrypt(val))
                    except Exception:
                        decrypted_gems[color] = 0
                else:
                    decrypted_gems[color] = int(val)
            player_doc["gems"] = GemType(**decrypted_gems)
        else:
            player_doc["gems"] = GemType(blue=0, green=0, red=0)

        player = Player(**player_doc)
        
        # Check if player is banned
        if player.is_banned:
            raise HTTPException(status_code=403, detail="Account is banned")

        # Update last login and IP
        await db.players.update_one(
            {"_id": player_doc.get("_id")},
            {
                "$set": {
                        "last_login": datetime.utcnow(),
                    "ip_address": client_ip or "unknown",
                    "device_fingerprint": device_fingerprint
                }
            }
        )

        # Create new session
        session = await token_manager.create_player_session(
            {"id":player_doc.get("_id"), **player_doc}, device_fingerprint or "unknown", client_ip or "unknown", user_agent or "unknown"    
        )
        # Generate tokens
        access_token = token_manager.create_access_token({"sub": str(player_doc.get("_id")), "wallet": player.wallet_address})
        refresh_token = session.refresh_token

        logger.info(f"Player logged in: {player.username}")

        # Set cookies
        set_auth_cookies(response, access_token, refresh_token)
        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60
        )
        print("player_doc7")    
        return token_response
        
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
        print("player_id",player_id)
        if not player_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Get player
        player_doc = await db.players.find_one({"_id":ObjectId(player_id)})
        if not player_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        player = Player(**player_doc)
        
        # Check if player is banned
        if player.is_banned:
            raise HTTPException(status_code=403, detail="Account is banned")
        
        # Generate new tokens
        access_token = token_manager.create_access_token({"sub": str(player_doc.get("_id")), "wallet": player.wallet_address})
        new_refresh_token = token_manager.create_refresh_token({"sub": str(player_doc.get("_id")), "wallet": player.wallet_address})
        
        # Update session
        await db.sessions.update_one(
            {"refresh_token": refresh_token},
            {"$set": {"refresh_token": new_refresh_token}}
        )
        
        logger.info(f"Token refreshed for player: {player.username}")
        
        # Set new cookies
        set_auth_cookies(response, access_token, new_refresh_token)
        
        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.access_token_expire_minutes * 60
        )
        return token_response
        
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
        
        logout_response = {"message": "Successfully logged out"}
        return logout_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

@router.get("/me", response_model=PlayerResponse)
async def get_current_player(request: Request, current_user: PlayerInfoSchema = Depends(get_current_user), db:AsyncIOMotorDatabase = Depends(get_database)):
    """Get current player information."""
    try:
        player_id = current_user.id
        if not player_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        print("player_id", player_id)
        print("player_info",current_user)
        # Use the already decrypted current_user data instead of fetching again
        response = PlayerResponse(
            id=str(current_user.id),
            wallet_address=current_user.wallet_address or "",
            username=current_user.username,
            email=current_user.email,
            token_balance=int(current_user.token_balance) if current_user.token_balance is not None else 0,
            total_games_played=current_user.total_games_played,
            total_tokens_earned=int(current_user.total_tokens_earned) if current_user.total_tokens_earned is not None else 0,
            total_tokens_spent=int(current_user.total_tokens_spent) if current_user.total_tokens_spent is not None else 0,
            gems=current_user.gems,
            is_active=current_user.is_active,
            created_at=current_user.created_at.isoformat() if current_user.created_at else None,
            last_login=current_user.last_login.isoformat() if current_user.last_login else None,
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger("app.routes.auth")
        logger.error(f"Get current player failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get player information")

                        
@router.post("/forgot-password")
async def forgot_password(request_data: ForgotPasswordRequest = Depends(decrypt_body(ForgotPasswordRequest)), db: AsyncIOMotorDatabase = Depends(get_database)):
    """Send OTP to email for password reset."""
    try:
        # Check if email exists in database
        user_doc = await db.players.find_one({"email": request_data.email})
        if not user_doc:
            print("user_doc",user_doc)
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
        email_sent = await email_manager.send_otp_email(request_data.email, user_doc.get("username", "User"), otp,MailType.FORGOTPASSWORD.value)
        if not email_sent:
            raise HTTPException(status_code=500, detail="Failed to send OTP email")
        logger.info(f"OTP sent to {request_data.email} for user {user_doc['_id']}")
        return {"message": "OTP sent successfully to your email"}
    except HTTPException as e:
        print("eeeeeee",e)
        raise
    except Exception as e:
        logger.error(f"Forgot password failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process forgot password request")

@router.post("/verify-otp")
async def verify_otp(request_data: VerifyOTPRequest= Depends(decrypt_body(VerifyOTPRequest)), db: AsyncIOMotorDatabase = Depends(get_database)):
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
async def reset_password(request_data: ResetPasswordRequest= Depends(decrypt_body(ResetPasswordRequest)), db: AsyncIOMotorDatabase = Depends(get_database)):
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




