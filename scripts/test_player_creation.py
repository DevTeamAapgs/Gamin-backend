#!/usr/bin/env python3
"""
Test script for player creation with role name functionality
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.schemas.player import PlayerCreate

def test_player_create_schema():
    """Test the PlayerCreate schema with role name"""
    
    print("Testing PlayerCreate Schema")
    print("=" * 40)
    
    # Test valid data with role name
    try:
        player_data = PlayerCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
            role="admin",  # Using role name instead of fk_role_id
            status=1
        )
        print(f"✓ Valid player data created: {player_data}")
        print(f"  Username: {player_data.username}")
        print(f"  Email: {player_data.email}")
        print(f"  Role: {player_data.role}")
        print(f"  Status: {player_data.status}")
        
    except Exception as e:
        print(f"✗ Error creating player data: {e}")
    
    # Test with different role
    try:
        player_data = PlayerCreate(
            username="testuser2",
            email="test2@example.com",
            password="password123",
            role="player",  # Different role
            status=1
        )
        print(f"✓ Valid player data with 'player' role: {player_data.role}")
        
    except Exception as e:
        print(f"✗ Error creating player data with 'player' role: {e}")

def test_request_body_format():
    """Test the expected request body format"""
    
    print("\nExpected Request Body Format")
    print("=" * 40)
    
    expected_format = {
        "username": "string",
        "email": "user@example.com",
        "password": "string",
        "role": "string",  # Role name instead of fk_role_id
        "status": 1
    }
    
    print("Expected request body:")
    for key, value in expected_format.items():
        print(f"  {key}: {value}")
    
    print("\nExample requests:")
    print("1. Create admin user:")
    admin_example = {
        "username": "admin_user",
        "email": "admin@example.com",
        "password": "secure_password",
        "role": "admin",
        "status": 1
    }
    print(f"   {admin_example}")
    
    print("\n2. Create regular player:")
    player_example = {
        "username": "regular_player",
        "email": "player@example.com",
        "password": "player_password",
        "role": "player",
        "status": 1
    }
    print(f"   {player_example}")

if __name__ == "__main__":
    test_player_create_schema()
    test_request_body_format()
    print("\n✓ Player creation schema tests completed!") 