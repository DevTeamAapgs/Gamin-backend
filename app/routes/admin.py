from fastapi import APIRouter, Body, HTTPException, Depends, Query, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.schemas.game import GameLevelUpdate, LeaderboardResponse
from app.schemas.player import AdminLogin, AdminCreate, PlayerInfoSchema
from app.auth.token_manager import token_manager
from app.models.player import Player,PlayerResponse
import time
from app.auth.cookie_auth import verify_admin, get_current_user
from app.utils.cookie_utils import set_auth_cookies, clear_auth_cookies
from app.services.analytics import analytics_service
from app.db.mongo import db, get_database
from app.services.logging_service import logging_service
from app.core.config import settings
from datetime import datetime, timedelta
import logging
from typing import Annotated, Callable, Optional, List
from passlib.context import CryptContext
from bson import ObjectId
from app.models.adminschemas import TokenResponse, AdminResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.player import CustomPlayerResponse, MenuItem, PermissionItem
from app.core.enums import PlayerType
from app.auth.cookie_auth import get_current_user, get_current_user_optional


from app.utils.crypto_dependencies import EncryptedBody, decrypt_body, decrypt_data_param
from app.schemas.player import BanRequest

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

@router.post("/login", response_model=TokenResponse  )
async def admin_login( response: Response ,    admin_data: AdminLogin = Depends(decrypt_body(AdminLogin)), db:AsyncIOMotorDatabase = Depends(get_database)):
    """Admin login with username and password."""
    try:
        print(admin_data,"admin_data")
    
        # Find admin by username
        admin_doc = await db.players.find_one({
            "email": admin_data.username,
            "player_type": {"$in": [PlayerType.ADMINEMPLOYEE,PlayerType.SUPERADMIN]}  # Allow both SUPERADMIN and ADMINEMPLOYEE
        })
        print("admin_doc",admin_doc)

       
        if not admin_doc:
            raise HTTPException(status_code=401, detail="Invalid credentials")
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
            "player_type": admin_doc.get("player_type", PlayerType.ADMINEMPLOYEE)
        })
        
        # Create refresh token
        refresh_token = token_manager.create_refresh_token({
            "sub": str(admin_doc["_id"]),
            "username": admin_doc["username"],
            "player_type": admin_doc.get("player_type", PlayerType.ADMINEMPLOYEE)
        })
        
        logger.info(f"Admin logged in: {admin_doc['username']}")
        
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
        logger.error(f"Admin login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/create", response_model=AdminResponse )
async def create_admin(
    request: Request,
    admin_data: AdminCreate = Depends(decrypt_body(AdminCreate)),
    db:AsyncIOMotorDatabase = Depends(get_database),
    current_admin: dict = Depends(verify_admin), 
):
    """Create a new admin user (requires existing admin authentication)."""
    try:
       
        
        # Check if admin already exists
        existing_admin = await db.players.find_one({
            "username": admin_data.username,
            "player_type": {"$in": [PlayerType.ADMINEMPLOYEE,PlayerType.SUPERADMIN]}  # Allow both SUPERADMIN and ADMINEMPLOYEE
        })
        
        if existing_admin:
            raise HTTPException(status_code=400, detail="Admin already exists")
        
        # Create new admin
        admin_user = {
            "username": admin_data.username,
            "email": admin_data.email,
            "password_hash": get_password_hash(admin_data.password),
            "wallet_address": None,  # Placeholder
            "player_type": 1,
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
        
        response = AdminResponse(
            id=str(admin_user["_id"]),
            username=admin_user["username"],
            email=admin_user["email"],
            is_admin=True,  # Always True for admin users
            is_active=admin_user["is_active"],
            created_at=admin_user["created_at"],
            last_login=admin_user["last_login"]
        )
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create admin failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create admin")

@router.get("/me", response_model=CustomPlayerResponse)
async def get_current_player(
    request: Request,
    current_user: PlayerInfoSchema = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    
    start_time = time.time()
    
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

            # Step 1: Extract permitted menu IDs from raw_permissions
        permitted_menu_ids = {
            perm["fk_menu_id"] for perm in raw_permissions if perm.get("can_access")
        }

        # Step 2: Fetch all permitted menu documents
        permitted_menu_docs = await db.menu_master.find({
            "_id": {"$in": [ObjectId(mid) for mid in permitted_menu_ids]}
        }).to_list(None)

        # Step 3: Build menu_map from permitted menus
        menu_map = {str(m["_id"]): m for m in permitted_menu_docs}

        # Step 4: Fetch missing parent menus
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

        # Step 5: Filter top-level menus with their own can_view permission
        top_menus = []
        for m in menu_map.values():
            if m["menu_type"] != 1:
                continue
            menu_id = str(m["_id"])
            for perm in raw_permissions:
                perm_id = perm["fk_menu_id"]
                if perm_id in menu_map:
                    perm_menu = menu_map[perm_id]
                    if (
                        perm_menu.get("menu_type") == 3 and
                        perm_menu.get("menu_value") == "can_view" and
                        str(perm_menu.get("fk_parent_id")) == menu_id
                    ):
                        top_menus.append(m)
                        break

        response_data = []

        # Step 6: Build final structured response
        for top_menu in top_menus:
            top_id = str(top_menu["_id"])

            # Collect top menu permissions
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

            # Collect submenus that have a can_view permission
            submenus = []
            for sm in menu_map.values():
                if sm.get("menu_type") == 2 and str(sm.get("fk_parent_id")) == top_id:
                    submenu_id = str(sm["_id"])
                    submenu_permissions = []
                    has_can_view = False

                    for perm in raw_permissions:
                        if perm["fk_menu_id"] in menu_map:
                            perm_menu = menu_map[perm["fk_menu_id"]]
                            if perm_menu.get("menu_type") == 3 and str(perm_menu.get("fk_parent_id")) == submenu_id:
                                if perm_menu.get("menu_value") == "can_view":
                                    has_can_view = True
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

                    if has_can_view:
                        submenus.append(MenuItem(
                            id=submenu_id,
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

            # Add final top-level menu to response
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
        end_time = time.time()
        print(f"Time taken for /me API: {end_time - start_time:.3f} seconds")
        # Final Response
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

@router.post("/refresh", response_model=TokenResponse)
async def admin_refresh_token(request: Request, response: Response ,  db:AsyncIOMotorDatabase = Depends(get_database)):
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
        if payload.get("player_type") not in [PlayerType.ADMINEMPLOYEE,PlayerType.SUPERADMIN]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        admin_id = payload.get("sub")
        username = payload.get("username")
        
        if not admin_id or not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Get admin from database
        
        admin_doc = await db.players.find_one({
            "_id": ObjectId(admin_id),
            "player_type": {"$in": [PlayerType.ADMINEMPLOYEE,PlayerType.SUPERADMIN]},  # Allow both SUPERADMIN and ADMINEMPLOYEE
            "is_active": True
        })
        
        if not admin_doc:
            raise HTTPException(status_code=404, detail="Admin not found or inactive")
        
        # Generate new tokens
        access_token = token_manager.create_access_token({
            "sub": str(admin_doc["_id"]), 
            "username": admin_doc["username"],
            "player_type": admin_doc.get("player_type", PlayerType.SUPERADMIN) in [PlayerType.ADMINEMPLOYEE,PlayerType.SUPERADMIN],
            "is_admin": admin_doc.get("is_admin", True)
        })
        
        new_refresh_token = token_manager.create_refresh_token({
            "sub": str(admin_doc["_id"]),
            "username": admin_doc["username"],
            "player_type": admin_doc.get("player_type",PlayerType.SUPERADMIN) in [PlayerType.ADMINEMPLOYEE,PlayerType.SUPERADMIN]
        })
        
        logger.info(f"Admin token refreshed: {admin_doc['username']}")
        
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
        logger.error(f"Admin token refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")

@router.post("/logout")
async def admin_logout(request: Request, response: Response):
    """Admin logout - clear authentication cookies."""
    try:
        # Clear authentication cookies
        clear_auth_cookies(response)
        
        logger.info("Admin logged out successfully")
        
        logout_response = {"message": "Successfully logged out"}
        return logout_response
        
    except Exception as e:
        logger.error(f"Admin logout failed: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

@router.get("/dashboard")
async def get_admin_dashboard(request: Request, current_admin: dict = Depends(verify_admin), db:AsyncIOMotorDatabase = Depends(get_database)):
    """Get admin dashboard data."""
    try:
        # Get platform analytics
        platform_stats = await analytics_service.get_platform_analytics()
        
        response_data = {
            "platform_stats": platform_stats,
            "timestamp": datetime.utcnow()
        }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get admin dashboard failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get admin dashboard")

@router.get("/analytics/platform")
async def get_platform_analytics(request: Request, current_admin: dict = Depends(verify_admin), db:AsyncIOMotorDatabase = Depends(get_database)):
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
    request: Request,
    game_type: str,
    level: int,
    time_range: str = "24h",
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db:AsyncIOMotorDatabase = Depends(get_database),
):
    """Get heatmap data for game interactions."""
    try:
        await verify_admin(request, credentials)
        
        heatmap_data = await analytics_service.generate_heatmap_data(game_type, level, time_range)
        
        return heatmap_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get heatmap data failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get heatmap data")

@router.put("/levels/{level_id}")
async def update_game_level(
    request: Request,
    level_id: str,
    level_data: GameLevelUpdate = Depends(decrypt_body(GameLevelUpdate)),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db:AsyncIOMotorDatabase = Depends(get_database),
):
    """Update game level configuration."""
    try:
        await verify_admin(request, credentials)
        
        
        
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
            
            response_data = {"message": "Game level updated successfully"}
            return response_data
        else:
            response_data = {"message": "No changes to update"}
            return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update game level failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to update game level")

@router.get("/players")
async def get_all_players(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    limit: int = 50,
    offset: int = 0,
    is_banned: Optional[bool] = None,
    db:AsyncIOMotorDatabase = Depends(get_database),
):
    """Get all players with optional filtering."""
    try:
        await verify_admin(request, credentials)
        # Build query
        query = {}
        if is_banned is not None:
            query["is_banned"] = is_banned
        
        # Get players
        players = await db.players.find(query).skip(offset).limit(limit).to_list(length=limit)
        total_count = await db.players.count_documents(query)
        
        response_data = {
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
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get all players failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get players")

@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    page: int = 1,
    page_size: int = 20,
    db:AsyncIOMotorDatabase = Depends(get_database),
):
    """Get platform leaderboard."""
    try:
        await verify_admin(request, credentials)
        
        
        
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
        
        response_data = LeaderboardResponse(
            entries=entries,
            total_players=total_players,
            page=page,
            page_size=page_size
        )
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get leaderboard failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get leaderboard")

@router.get("/transactions")
async def get_all_transactions(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    limit: int = 50,
    offset: int = 0,
    transaction_type: Optional[str] = None,
    db:AsyncIOMotorDatabase = Depends(get_database),
):
    """Get all transactions."""
    try:
        await verify_admin(request, credentials)
        
        
        
        # Build query
        query = {}
        if transaction_type:
            query["transaction_type"] = transaction_type
        
        # Get transactions
        transactions = await db.transactions.find(query).sort("created_at", -1).skip(offset).limit(limit).to_list(length=limit)
        total_count = await db.transactions.count_documents(query)
        
        response_data = {
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
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get all transactions failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get transactions")

@router.get("/logs/requests")
async def get_request_logs(
    request: Request,
    player_id: Optional[str] = Query(None, description="Filter by player ID"),
    path: Optional[str] = Query(None, description="Filter by path"),
    status_code: Optional[int] = Query(None, description="Filter by status code"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(100, le=1000, description="Number of logs to return"),
    admin_token: dict = Depends(verify_admin),
    db:AsyncIOMotorDatabase = Depends(get_database),
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
        
        response_data = {
            "success": True,
            "data": logs,
            "count": len(logs)
        }
        return response_data
    except Exception as e:
        logger.error(f"Failed to get request logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve request logs")

@router.get("/logs/security")
async def get_security_logs(
    request: Request,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    player_id: Optional[str] = Query(None, description="Filter by player ID"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(100, le=1000, description="Number of logs to return"),
    admin_token: dict = Depends(verify_admin),
    db:AsyncIOMotorDatabase = Depends(get_database),
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
        
        response_data = {
            "success": True,
            "data": logs,
            "count": len(logs)
        }
        return response_data
    except Exception as e:
        logger.error(f"Failed to get security logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve security logs")

@router.get("/logs/game-actions")
async def get_game_action_logs(
    request: Request,
    game_id: Optional[str] = Query(None, description="Filter by game ID"),
    player_id: Optional[str] = Query(None, description="Filter by player ID"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(100, le=1000, description="Number of logs to return"),
    admin_token: dict = Depends(verify_admin),
    db:AsyncIOMotorDatabase = Depends(get_database),
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
        
        response_data = {
            "success": True,
            "data": logs,
            "count": len(logs)
        }
        return response_data
    except Exception as e:
        logger.error(f"Failed to get game action logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve game action logs")

@router.get("/logs/statistics")
async def get_log_statistics(
    request: Request,
    admin_token: dict = Depends(verify_admin),
    db:AsyncIOMotorDatabase = Depends(get_database),
):
    """Get logging statistics and metrics."""
    try:
        stats = await logging_service.get_log_statistics()
        
        response_data = {
            "success": True,
            "data": stats
        }
        return response_data
    except Exception as e:
        logger.error(f"Failed to get log statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve log statistics")

@router.post("/logs/cleanup")
async def cleanup_old_logs(
    request: Request,
    admin_token: dict = Depends(verify_admin),
    db:AsyncIOMotorDatabase = Depends(get_database),
):
    """Clean up old logs based on TTL."""
    try:
        result = await logging_service.cleanup_old_logs()
        
        response_data = {
            "success": True,
            "data": result,
            "message": "Log cleanup completed successfully"
        }
        return response_data
    except Exception as e:
        logger.error(f"Failed to cleanup logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup logs")

@router.get("/logs/export")
async def export_logs(
    request: Request,
    log_type: str = Query(..., description="Type of logs to export: requests, security, game-actions"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    format: str = Query("json", description="Export format: json, csv"),
    admin_token: dict = Depends(verify_admin),
    db:AsyncIOMotorDatabase = Depends(get_database),
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
            
            response_data = {
                "success": True,
                "data": output.getvalue(),
                "format": "csv",
                "filename": f"{log_type}_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        else:
            response_data = {
                "success": True,
                "data": logs,
                "format": "json",
                "count": len(logs)
            }
        
        return response_data
            
    except Exception as e:
        logger.error(f"Failed to export logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to export logs") 