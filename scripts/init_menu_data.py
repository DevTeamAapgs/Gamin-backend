#!/usr/bin/env python3
"""
Script to initialize menu master data for the gaming platform.
This script creates the hierarchical menu structure as described in the requirements.
"""

import asyncio
import sys
import os
from datetime import datetime
from bson import ObjectId

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.mongo import connect_to_mongo, close_mongo_connection, get_database
from app.services.menu_service import MenuService
from app.schemas.menu import MenuCreate

async def init_menu_data():
    """Initialize menu master data"""
    print("Connecting to MongoDB...")
    await connect_to_mongo()
    
    try:
        menu_service = MenuService()
        
        # Check if menu data already exists
        existing_count = await menu_service.collection.count_documents({})
        if existing_count > 0:
            print(f"Menu data already exists ({existing_count} items). Skipping initialization.")
            return
        
        print("Creating menu master data...")
        
        # Create main menu items (menu_type = 1)
        dashboard_menu = MenuCreate(
            menu_name="UI.DASHBOARD",
            menu_value="dashboard",
            menu_type=1,
            menu_order=1,
            fk_parent_id=None,
            can_show=1,
            router_url="",
            menu_icon="solar:home-smile-angle-outline",
            active_urls=[],
            mobile_access=1,
            can_view=1,
            can_add=0,
            can_edit=0,
            can_delete=0,
            description="Main dashboard menu item",
            module="dashboard"
        )
        
        user_management_menu = MenuCreate(
            menu_name="UI.USERMANAGEMENT",
            menu_value="user_management",
            menu_type=1,
            menu_order=2,
            fk_parent_id=None,
            can_show=1,
            router_url="",
            menu_icon="flowbite:users-group-outline",
            active_urls=[],
            mobile_access=1,
            can_view=1,
            can_add=0,
            can_edit=0,
            can_delete=0,
            description="User management main menu item",
            module="user_management"
        )
        
        # Create main menu items
        dashboard_response = await menu_service.create_menu(dashboard_menu)
        user_management_response = await menu_service.create_menu(user_management_menu)
        
        print(f"Created main menu items:")
        print(f"  - Dashboard: {dashboard_response.menu_value} (ID: {dashboard_response.id})")
        print(f"  - User Management: {user_management_response.menu_value} (ID: {user_management_response.id})")
        
        # Create sub-menu items (menu_type = 2) for User Management
        users_submenu = MenuCreate(
            menu_name="UI.USER",
            menu_value="user",
            menu_type=2,
            menu_order=1,
            fk_parent_id=user_management_response.id,
            can_show=1,
            router_url="/hr-management/hrmanagement/user",
            menu_icon="",
            active_urls=[
                "/hr-management/hrmanagement/user-view",
                "/hr-management/hrmanagement/user-edit/:id",
                "/hr-management/hrmanagement/user-add",
                "/hr-management/hrmanagement/user-delete/:id"
            ],
            mobile_access=1,
            can_view=1,
            can_add=1,
            can_edit=1,
            can_delete=1,
            description="User management sub-menu",
            module="user_management"
        )
        
        roles_submenu = MenuCreate(
            menu_name="UI.ROLES",
            menu_value="roles",
            menu_type=2,
            menu_order=2,
            fk_parent_id=user_management_response.id,
            can_show=1,
            router_url="/hr-management/hrmanagement/roles",
            menu_icon="",
            active_urls=[
                "/hr-management/hrmanagement/roles-view",
                "/hr-management/hrmanagement/roles-edit/:id",
                "/hr-management/hrmanagement/roles-add",
                "/hr-management/hrmanagement/roles-delete/:id"
            ],
            mobile_access=1,
            can_view=1,
            can_add=1,
            can_edit=1,
            can_delete=1,
            description="Roles management sub-menu",
            module="user_management"
        )
        
        # Create sub-menu items
        users_response = await menu_service.create_menu(users_submenu)
        roles_response = await menu_service.create_menu(roles_submenu)
        
        print(f"Created sub-menu items:")
        print(f"  - Users: {users_response.menu_value} (ID: {users_response.id})")
        print(f"  - Roles: {roles_response.menu_value} (ID: {roles_response.id})")
        
        # Create additional menu items for a complete gaming platform
        game_menu = MenuCreate(
            menu_name="UI.GAME",
            menu_value="game",
            menu_type=1,
            menu_order=3,
            fk_parent_id=None,
            can_show=1,
            router_url="",
            menu_icon="game-icons:gamepad-cross",
            active_urls=[],
            mobile_access=1,
            can_view=1,
            can_add=0,
            can_edit=0,
            can_delete=0,
            description="Game management main menu item",
            module="game"
        )
        
        analytics_menu = MenuCreate(
            menu_name="UI.ANALYTICS",
            menu_value="analytics",
            menu_type=1,
            menu_order=4,
            fk_parent_id=None,
            can_show=1,
            router_url="",
            menu_icon="material-symbols:analytics-outline",
            active_urls=[],
            mobile_access=1,
            can_view=1,
            can_add=0,
            can_edit=0,
            can_delete=0,
            description="Analytics main menu item",
            module="analytics"
        )
        
        # Create additional main menu items
        game_response = await menu_service.create_menu(game_menu)
        analytics_response = await menu_service.create_menu(analytics_menu)
        
        print(f"Created additional main menu items:")
        print(f"  - Game: {game_response.menu_value} (ID: {game_response.id})")
        print(f"  - Analytics: {analytics_response.menu_value} (ID: {analytics_response.id})")
        
        # Create sub-menu items for Game
        game_list_submenu = MenuCreate(
            menu_name="UI.GAME_LIST",
            menu_value="game_list",
            menu_type=2,
            menu_order=1,
            fk_parent_id=game_response.id,
            can_show=1,
            router_url="/game-management/games",
            menu_icon="",
            active_urls=[
                "/game-management/games-view",
                "/game-management/games-edit/:id",
                "/game-management/games-add",
                "/game-management/games-delete/:id"
            ],
            mobile_access=1,
            can_view=1,
            can_add=1,
            can_edit=1,
            can_delete=1,
            description="Game list management",
            module="game"
        )
        
        game_settings_submenu = MenuCreate(
            menu_name="UI.GAME_SETTINGS",
            menu_value="game_settings",
            menu_type=2,
            menu_order=2,
            fk_parent_id=game_response.id,
            can_show=1,
            router_url="/game-management/settings",
            menu_icon="",
            active_urls=[
                "/game-management/settings-view",
                "/game-management/settings-edit/:id"
            ],
            mobile_access=1,
            can_view=1,
            can_add=0,
            can_edit=1,
            can_delete=0,
            description="Game settings management",
            module="game"
        )
        
        # Create game sub-menu items
        game_list_response = await menu_service.create_menu(game_list_submenu)
        game_settings_response = await menu_service.create_menu(game_settings_submenu)
        
        print(f"Created game sub-menu items:")
        print(f"  - Game List: {game_list_response.menu_value} (ID: {game_list_response.id})")
        print(f"  - Game Settings: {game_settings_response.menu_value} (ID: {game_settings_response.id})")
        
        # Create sub-menu items for Analytics
        player_analytics_submenu = MenuCreate(
            menu_name="UI.PLAYER_ANALYTICS",
            menu_value="player_analytics",
            menu_type=2,
            menu_order=1,
            fk_parent_id=analytics_response.id,
            can_show=1,
            router_url="/analytics/players",
            menu_icon="",
            active_urls=[
                "/analytics/players-view",
                "/analytics/players-export"
            ],
            mobile_access=1,
            can_view=1,
            can_add=0,
            can_edit=0,
            can_delete=0,
            description="Player analytics",
            module="analytics"
        )
        
        game_analytics_submenu = MenuCreate(
            menu_name="UI.GAME_ANALYTICS",
            menu_value="game_analytics",
            menu_type=2,
            menu_order=2,
            fk_parent_id=analytics_response.id,
            can_show=1,
            router_url="/analytics/games",
            menu_icon="",
            active_urls=[
                "/analytics/games-view",
                "/analytics/games-export"
            ],
            mobile_access=1,
            can_view=1,
            can_add=0,
            can_edit=0,
            can_delete=0,
            description="Game analytics",
            module="analytics"
        )
        
        # Create analytics sub-menu items
        player_analytics_response = await menu_service.create_menu(player_analytics_submenu)
        game_analytics_response = await menu_service.create_menu(game_analytics_submenu)
        
        print(f"Created analytics sub-menu items:")
        print(f"  - Player Analytics: {player_analytics_response.menu_value} (ID: {player_analytics_response.id})")
        print(f"  - Game Analytics: {game_analytics_response.menu_value} (ID: {game_analytics_response.id})")
        
        # Verify the menu tree
        print("\nVerifying menu tree structure...")
        menu_tree = await menu_service.get_menu_tree()
        
        print(f"Menu tree created successfully with {len(menu_tree)} root items:")
        for root_menu in menu_tree:
            print(f"  - {root_menu.menu_name} ({root_menu.menu_value})")
            for child in root_menu.children:
                print(f"    └─ {child.menu_name} ({child.menu_value})")
        
        print("\nMenu master data initialization completed successfully!")
        
    except Exception as e:
        print(f"Error initializing menu data: {str(e)}")
        raise
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(init_menu_data()) 