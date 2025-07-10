#!/usr/bin/env python3
"""
Comprehensive test script for Admin CRUD functionality
Tests authentication, listing, creating, updating, and deleting admins
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class AdminCRUDTester:
    def __init__(self):
        self.session = None
        self.cookies = {}
        self.test_admin_id = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def login_admin(self):
        """Login as admin and get cookies"""
        print("🔐 Logging in as admin...")
        
        login_data = {
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }
        
        async with self.session.post(
            f"{BASE_URL}/api/v1/admin/login",
            json=login_data
        ) as response:
            if response.status == 200:
                # Get cookies from response
                cookies = response.cookies
                for cookie in cookies:
                    self.cookies[cookie.key] = cookie.value
                print("✅ Admin login successful")
                return True
            else:
                print(f"❌ Admin login failed: {response.status}")
                return False
    
    async def test_list_admins(self):
        """Test listing admins with different filters"""
        print("\n📋 Testing admin listing...")
        
        # Test 1: Basic listing
        print("  Testing basic listing...")
        async with self.session.get(
            f"{BASE_URL}/api/v1/admincrud/admins?page=1&count=5",
            cookies=self.cookies
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"    ✅ Basic listing: {len(data['items'])} admins returned")
                print(f"    Total admins: {data['pagination']['total']}")
            else:
                print(f"    ❌ Basic listing failed: {response.status}")
        
        # Test 2: Search by username
        print("  Testing search by username...")
        async with self.session.get(
            f"{BASE_URL}/api/v1/admincrud/admins?search_string=admin&page=1&count=10",
            cookies=self.cookies
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"    ✅ Search by 'admin': {len(data['items'])} results")
            else:
                print(f"    ❌ Search failed: {response.status}")
        
        # Test 3: Filter by status
        print("  Testing status filter...")
        async with self.session.get(
            f"{BASE_URL}/api/v1/admincrud/admins?status=1&page=1&count=10",
            cookies=self.cookies
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"    ✅ Status filter (active): {len(data['items'])} results")
            else:
                print(f"    ❌ Status filter failed: {response.status}")
        
        # Test 4: Filter by role
        print("  Testing role filter...")
        async with self.session.get(
            f"{BASE_URL}/api/v1/admincrud/admins?role=admin&page=1&count=10",
            cookies=self.cookies
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"    ✅ Role filter (admin): {len(data['items'])} results")
            else:
                print(f"    ❌ Role filter failed: {response.status}")
    
    async def test_create_admin(self):
        """Test creating a new admin"""
        print("\n➕ Testing admin creation...")
        
        # Create form data
        data = aiohttp.FormData()
        data.add_field('username', f'testadmin_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        data.add_field('email', f'testadmin_{datetime.now().strftime("%Y%m%d_%H%M%S")}@example.com')
        data.add_field('password', 'password123')
        data.add_field('role', 'admin')
        
        async with self.session.post(
            f"{BASE_URL}/api/v1/admincrud/admins",
            data=data,
            cookies=self.cookies
        ) as response:
            if response.status == 200:
                admin_data = await response.json()
                self.test_admin_id = admin_data['id']
                print(f"    ✅ Admin created successfully: {admin_data['username']}")
                print(f"    Admin ID: {self.test_admin_id}")
                print(f"    Player Prefix: {admin_data.get('player_prefix', 'None')}")
                return True
            else:
                error_text = await response.text()
                print(f"    ❌ Admin creation failed: {response.status}")
                print(f"    Error: {error_text}")
                return False
    
    async def test_get_admin(self):
        """Test getting a specific admin"""
        if not self.test_admin_id:
            print("    ⚠️  Skipping get admin test - no admin created")
            return
            
        print("\n👤 Testing get admin...")
        
        async with self.session.get(
            f"{BASE_URL}/api/v1/admincrud/admins/{self.test_admin_id}",
            cookies=self.cookies
        ) as response:
            if response.status == 200:
                admin_data = await response.json()
                print(f"    ✅ Get admin successful: {admin_data['username']}")
                print(f"    Role: {admin_data.get('role', 'None')}")
                print(f"    Player Prefix: {admin_data.get('player_prefix', 'None')}")
            else:
                print(f"    ❌ Get admin failed: {response.status}")
    
    async def test_update_admin(self):
        """Test updating an admin"""
        if not self.test_admin_id:
            print("    ⚠️  Skipping update admin test - no admin created")
            return
            
        print("\n✏️  Testing admin update...")
        
        # Update form data
        data = aiohttp.FormData()
        data.add_field('email', f'updated_{datetime.now().strftime("%Y%m%d_%H%M%S")}@example.com')
        data.add_field('role', 'manager')
        
        async with self.session.put(
            f"{BASE_URL}/api/v1/admincrud/admins/{self.test_admin_id}",
            data=data,
            cookies=self.cookies
        ) as response:
            if response.status == 200:
                admin_data = await response.json()
                print(f"    ✅ Admin update successful: {admin_data['email']}")
                print(f"    Updated Role: {admin_data.get('role', 'None')}")
            else:
                error_text = await response.text()
                print(f"    ❌ Admin update failed: {response.status}")
                print(f"    Error: {error_text}")
    
    async def test_update_admin_status(self):
        """Test updating admin status"""
        if not self.test_admin_id:
            print("    ⚠️  Skipping status update test - no admin created")
            return
            
        print("\n🔄 Testing admin status update...")
        
        status_data = {"status": 0}  # Set to inactive
        
        async with self.session.patch(
            f"{BASE_URL}/api/v1/admincrud/admins/{self.test_admin_id}/status",
            json=status_data,
            cookies=self.cookies
        ) as response:
            if response.status == 200:
                admin_data = await response.json()
                print(f"    ✅ Status update successful: {admin_data['status']}")
            else:
                print(f"    ❌ Status update failed: {response.status}")
    
    async def test_update_admin_role(self):
        """Test updating admin role"""
        if not self.test_admin_id:
            print("    ⚠️  Skipping role update test - no admin created")
            return
            
        print("\n🎭 Testing admin role update...")
        
        role_data = {"role": "admin"}
        
        async with self.session.patch(
            f"{BASE_URL}/api/v1/admincrud/admins/{self.test_admin_id}/role",
            json=role_data,
            cookies=self.cookies
        ) as response:
            if response.status == 200:
                admin_data = await response.json()
                print(f"    ✅ Role update successful: {admin_data.get('role', 'None')}")
            else:
                print(f"    ❌ Role update failed: {response.status}")
    
    async def test_delete_admin(self):
        """Test deleting an admin"""
        if not self.test_admin_id:
            print("    ⚠️  Skipping delete admin test - no admin created")
            return
            
        print("\n🗑️  Testing admin deletion...")
        
        async with self.session.delete(
            f"{BASE_URL}/api/v1/admincrud/admins/{self.test_admin_id}",
            cookies=self.cookies
        ) as response:
            if response.status == 200:
                print(f"    ✅ Admin deletion successful")
            else:
                print(f"    ❌ Admin deletion failed: {response.status}")
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Admin CRUD Comprehensive Test")
        print("=" * 50)
        
        # Test 1: Login
        if not await self.login_admin():
            print("❌ Cannot proceed without admin login")
            return
        
        # Test 2: List admins
        await self.test_list_admins()
        
        # Test 3: Create admin
        if await self.test_create_admin():
            # Test 4: Get admin
            await self.test_get_admin()
            
            # Test 5: Update admin
            await self.test_update_admin()
            
            # Test 6: Update status
            await self.test_update_admin_status()
            
            # Test 7: Update role
            await self.test_update_admin_role()
            
            # Test 8: Delete admin
            await self.test_delete_admin()
        
        print("\n" + "=" * 50)
        print("✅ Admin CRUD test completed!")

async def main():
    """Main test function"""
    async with AdminCRUDTester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    print("Admin CRUD Test Script")
    print("Make sure your server is running on http://localhost:8000")
    print("Press Enter to start testing...")
    input()
    
    asyncio.run(main()) 