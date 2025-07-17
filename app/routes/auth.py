from re import A
from traceback import print_tb
from fastapi import APIRouter, Body, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Any,Optional
from app.schemas.player import PlayerCreate, PlayerLogin, PlayerResponse
from app.models.player import Player,PlayerResponse
from app.auth.token_manager import token_manager
from app.auth.cookie_auth import get_current_user, get_current_user_optional
from app.utils.cookie_utils import set_auth_cookies, clear_auth_cookies
from app.utils.upload_handler import profile_pic_handler
from app.utils.email_utils import email_manager
from app.db.mongo import get_database
from app.core.config import settings
from datetime import datetime, timedelta
import logging
from app.db.mongo import get_database
from app.auth.cookie_auth import get_current_user
from typing import Annotated, Callable
import os
import shutil
from pathlib import Path
from app.core.enums import PlayerType

from app.utils.crypto_dependencies import decrypt_body
from app.models.adminschemas import TokenResponse, ForgotPasswordRequest, VerifyOTPRequest, ResetPasswordRequest
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

@router.post("/register", response_model=TokenResponse)
async def register_player(
    request: Request, 
    response: Response, 
    player_data: PlayerCreate = Depends(decrypt_body(PlayerCreate)), 
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Register a new player."""
    try:
        
        # Check if player already exists
        existing_player = await db.players.find_one({
            "$or": [
                {"username": player_data.username},
                {"email": player_data.email}
            ]
        })
        
        if existing_player:
            raise HTTPException(status_code=400, detail="Player already exists")
        
        # Create new player document
        player_doc = {
            "username": player_data.username,
            "email": player_data.email,
            "ip_address": request.client.host if request.client else "unknown"
        }
        
        # Save to database
        result = await db.players.insert_one(player_doc)
        player_id = result.inserted_id
        
        # Create Player object for session
        player_doc["_id"] = player_id
        player = Player(**player_doc)
        
        # Create session and tokens
        device_fingerprint = "default"
        session = await token_manager.create_player_session(
            player, device_fingerprint, request.client.host if request.client else "unknown"
        )
        
        # Generate tokens
        access_token = token_manager.create_access_token({"sub": str(player_id), "username": player_data.username})
        refresh_token = session.refresh_token
        
        logger.info(f"New player registered: {player_data.username}")
        
        # Set cookies
        set_auth_cookies(response, access_token, refresh_token)
        
        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60
        )
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login", response_model=TokenResponse)
async def login_player(  request: Request, response: Response, player_data: PlayerLogin = Depends(decrypt_body(PlayerLogin)), db:AsyncIOMotorDatabase = Depends(get_database)):
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
        
        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60
        )
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

@router.get("/me", response_model=CustomPlayerResponse)
async def get_current_player(
    request: Request,
    current_user: Player = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        print(current_user)

        # Handle superadmin
        if current_user.player_type == PlayerType.SUPERADMIN:
            # Superadmin: fetch all menus
            all_menus = await db.menu_master.find({}).to_list(None)

            menu_map = {str(m["_id"]): m for m in all_menus}

            top_menus = [m for m in all_menus if m["menu_type"] == 1]
            response_data = []

            for top_menu in top_menus:
                top_id = str(top_menu["_id"])

                # Get direct permissions
                permissions = [
                    PermissionItem(
                        id=str(p["_id"]),
                        menu_name=p.get("menu_name"),
                        menu_value=p.get("menu_value"),
                        menu_type=p.get("menu_type"),
                        menu_order=p.get("menu_order"),
                        fk_parent_id=str(p.get("fk_parent_id")),
                        description=p.get("description"),
                        can_access=True,
                        router_url=p.get("router_url", "")
                    )
                    for p in all_menus
                    if p.get("menu_type") == 3 and str(p.get("fk_parent_id")) == top_id
                ]

                # Get submenus and their permissions
                submenus = []
                for sm in all_menus:
                    if sm.get("menu_type") == 2 and str(sm.get("fk_parent_id")) == top_id:
                        submenu_permissions = [
                            PermissionItem(
                                id=str(p["_id"]),
                                menu_name=p.get("menu_name"),
                                menu_value=p.get("menu_value"),
                                menu_type=p.get("menu_type"),
                                menu_order=p.get("menu_order"),
                                fk_parent_id=str(p.get("fk_parent_id")),
                                description=p.get("description"),
                                can_access=True,
                                router_url=p.get("router_url", "")
                            )
                            for p in all_menus
                            if p.get("menu_type") == 3 and str(p.get("fk_parent_id")) == str(sm["_id"])
                        ]

                        submenus.append(MenuItem(
                            id=str(sm["_id"]),
                            menu_name=sm.get("menu_name"),
                            menu_value=sm.get("menu_value"),
                            menu_type=sm.get("menu_type"),
                            menu_order=sm.get("menu_order"),
                            fk_parent_id=str(sm.get("fk_parent_id")),
                            can_show=sm.get("can_show"),
                            router_url=sm.get("router_url"),
                            menu_icon=sm.get("menu_icon"),
                            active_urls=sm.get("active_urls", []),
                            mobile_access=sm.get("mobile_access"),
                            permission=submenu_permissions,
                            submenu=[]
                        ))

                response_data.append(MenuItem(
                    id=top_id,
                    menu_name=top_menu.get("menu_name"),
                    menu_value=top_menu.get("menu_value"),
                    menu_type=top_menu.get("menu_type"),
                    menu_order=top_menu.get("menu_order"),
                    fk_parent_id=top_menu.get("fk_parent_id"),
                    can_show=top_menu.get("can_show"),
                    router_url=top_menu.get("router_url"),
                    menu_icon=top_menu.get("menu_icon"),
                    active_urls=top_menu.get("active_urls", []),
                    mobile_access=top_menu.get("mobile_access"),
                    permission=permissions,
                    submenu=submenus
                ))

            return CustomPlayerResponse(
                page_count=len(response_data),
                response_data=response_data,
                full_name= current_user.username,
                profile_photo=current_user.profile_photo
            )

        # If not superadmin, check for role and permissions
        role_id = current_user.fk_role_id
        if not role_id:
            return CustomPlayerResponse(
                page_count=0,
                response_data=[],
                full_name=current_user.username,
                profile_photo=current_user.profile_photo
            )

        role_id = ObjectId(role_id) if isinstance(role_id, str) else role_id
        role_doc = await db.roles.find_one({"_id": role_id})
        if not role_doc:
            return CustomPlayerResponse(
                page_count=0,
                response_data=[],
                full_name=current_user.username,
                profile_photo=current_user.profile_photo
            )

        raw_permissions = role_doc.get("permissions", [])
        if not raw_permissions:
            return CustomPlayerResponse(
                page_count=0,
                response_data=[],
                full_name=current_user.username,
                profile_photo=current_user.profile_photo
            )

        # Step 1: get all permitted menu_ids
        permitted_menu_ids = {
            perm["fk_menu_id"] for perm in raw_permissions if perm.get("can_access")
        }

        # Step 2: fetch all permitted menus
        permitted_menu_docs = await db.menu_master.find({
            "_id": {"$in": [ObjectId(mid) for mid in permitted_menu_ids]}
        }).to_list(None)

        # Step 3: map them
        menu_map = {str(m["_id"]): m for m in permitted_menu_docs}

        # Step 4: fetch missing parents (of permission items)
        missing_parent_ids = {
            str(m.get("fk_parent_id"))
            for m in permitted_menu_docs
            if m.get("fk_parent_id") and str(m.get("fk_parent_id")) not in menu_map
        }

        if missing_parent_ids:
            parent_docs = await db.menu_master.find({
                "_id": {"$in": [ObjectId(mid) for mid in missing_parent_ids]}
            }).to_list(None)
            for m in parent_docs:
                menu_map[str(m["_id"])] = m

        # Step 5: find top-level menus (menu_type == 1) that have their own can_view permission
        top_menus = []
        for m in menu_map.values():
            if m["menu_type"] != 1:
                continue
            menu_id = str(m["_id"])

            # check if this menu has a permission with menu_type=3, value=can_view, fk_parent_id == menu_id
            for perm in raw_permissions:
                perm_id = perm["fk_menu_id"]
                if perm_id in menu_map:
                    perm_menu = menu_map[perm_id]
                    if perm_menu.get("menu_type") == 3 and perm_menu.get("menu_value") == "can_view":
                        if str(perm_menu.get("fk_parent_id")) == menu_id:
                            top_menus.append(m)
                            break

        response_data = []

        for top_menu in top_menus:
            top_id = str(top_menu["_id"])

            permissions = []
            for perm in raw_permissions:
                perm_id = perm["fk_menu_id"]
                if perm_id in menu_map:
                    p = menu_map[perm_id]
                    if p.get("menu_type") == 3 and str(p.get("fk_parent_id")) == top_id:
                        permissions.append(PermissionItem(
                            id=perm_id,
                            menu_name=p.get("menu_name"),
                            menu_value=p.get("menu_value"),
                            menu_type=p.get("menu_type"),
                            menu_order=p.get("menu_order"),
                            fk_parent_id=str(p.get("fk_parent_id")),
                            description=p.get("description"),
                            can_access=True,
                            router_url=p.get("router_url", "")
                        ))

            submenus = []
            for sm in menu_map.values():
                if sm.get("menu_type") == 2 and str(sm.get("fk_parent_id")) == top_id:
                    submenu_permissions = []
                    for perm in raw_permissions:
                        if perm["fk_menu_id"] in menu_map:
                            perm_menu = menu_map[perm["fk_menu_id"]]
                            if perm_menu.get("menu_type") == 3 and str(perm_menu.get("fk_parent_id")) == str(sm["_id"]):
                                submenu_permissions.append(PermissionItem(
                                    id=perm["fk_menu_id"],
                                    menu_name=perm_menu.get("menu_name"),
                                    menu_value=perm_menu.get("menu_value"),
                                    menu_type=perm_menu.get("menu_type"),
                                    menu_order=perm_menu.get("menu_order"),
                                    fk_parent_id=str(perm_menu.get("fk_parent_id")),
                                    description=perm_menu.get("description"),
                                    can_access=True,
                                    router_url=perm_menu.get("router_url", "")
                                ))
                    if submenu_permissions:
                        submenus.append(MenuItem(
                            id=str(sm["_id"]),
                            menu_name=sm.get("menu_name"),
                            menu_value=sm.get("menu_value"),
                            menu_type=sm.get("menu_type"),
                            menu_order=sm.get("menu_order"),
                            fk_parent_id=str(sm.get("fk_parent_id")),
                            can_show=sm.get("can_show"),
                            router_url=sm.get("router_url"),
                            menu_icon=sm.get("menu_icon"),
                            active_urls=sm.get("active_urls", []),
                            mobile_access=sm.get("mobile_access"),
                            permission=submenu_permissions,
                            submenu=[]
                        ))

            response_data.append(MenuItem(
                id=top_id,
                menu_name=top_menu.get("menu_name"),
                menu_value=top_menu.get("menu_value"),
                menu_type=top_menu.get("menu_type"),
                menu_order=top_menu.get("menu_order"),
                fk_parent_id=top_menu.get("fk_parent_id"),
                can_show=top_menu.get("can_show"),
                router_url=top_menu.get("router_url"),
                menu_icon=top_menu.get("menu_icon"),
                active_urls=top_menu.get("active_urls", []),
                mobile_access=top_menu.get("mobile_access"),
                permission=permissions,
                submenu=submenus
            ))

        return CustomPlayerResponse(
            page_count=len(response_data),
            response_data=response_data,
            full_name=current_user.username,
            profile_photo=current_user.profile_photo
        )

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




