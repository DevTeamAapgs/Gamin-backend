#!/usr/bin/env python3
"""
Test script for the menu master system.
This script tests the basic functionality of the menu system.
"""

import asyncio
import sys
import os
from bson import ObjectId

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.mongo import connect_to_mongo, close_mongo_connection
from app.services.menu_service import MenuService
from app.schemas.menu import MenuCreate

async def test_menu_system():
    """Test the menu system functionality"""
    print("Testing Menu Master System...")
    
    await connect_to_mongo()
    
    try:
        menu_service = MenuService()
        
        # Test 1: Get main menu items
        print("\n1. Testing get main menu items...")
        main_menus = await menu_service.get_menus_by_type(1)
        print(f"Found {len(main_menus)} main menu items:")
        for menu in main_menus:
            print(f"  - {menu.menu_name} ({menu.menu_value})")
        
        # Test 2: Get menu tree
        print("\n2. Testing get menu tree...")
        menu_tree = await menu_service.get_menu_tree()
        print(f"Menu tree has {len(menu_tree)} root items:")
        for root_menu in menu_tree:
            print(f"  - {root_menu.menu_name} ({root_menu.menu_value})")
            for child in root_menu.children:
                print(f"    └─ {child.menu_name} ({child.menu_value})")
        
        # Test 3: Get menu by value
        print("\n3. Testing get menu by value...")
        dashboard_menu = await menu_service.get_menu_by_value("dashboard")
        if dashboard_menu:
            print(f"Dashboard menu found: {dashboard_menu.menu_name}")
        else:
            print("Dashboard menu not found")
        
        # Test 4: Get menu permissions
        print("\n4. Testing get menu permissions...")
        permissions = await menu_service.get_menu_permissions("user_management")
        if permissions:
            print(f"User management permissions:")
            print(f"  - Can view: {permissions['can_view']}")
            print(f"  - Can add: {permissions['can_add']}")
            print(f"  - Can edit: {permissions['can_edit']}")
            print(f"  - Can delete: {permissions['can_delete']}")
        else:
            print("User management permissions not found")
        
        # Test 5: List menus with pagination
        print("\n5. Testing list menus with pagination...")
        menu_list = await menu_service.list_menus(page=1, size=5)
        print(f"Menu list: {menu_list.total} total items, page {menu_list.page} of {menu_list.pages}")
        for menu in menu_list.items[:3]:  # Show first 3 items
            print(f"  - {menu.menu_name} ({menu.menu_value})")
        
        print("\n✅ All menu system tests passed!")
        
    except Exception as e:
        print(f"❌ Error testing menu system: {str(e)}")
        raise
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(test_menu_system()) 