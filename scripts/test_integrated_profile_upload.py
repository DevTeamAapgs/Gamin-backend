#!/usr/bin/env python3
"""
Test script for integrated profile picture upload functionality
Tests both POST (create user) and PUT (update user) endpoints with profile picture upload
"""

import requests
import json
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000/api/v1/player"
TEST_IMAGE_PATH = "uploads/profile_686b5af8871b44ad08e74080_61ef137b.png"  # Use existing test image

def test_create_user_with_profile_pic():
    """Test creating a user with profile picture upload"""
    print("=== Testing POST /player/ with profile picture ===")
    
    # Check if test image exists
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"❌ Test image not found: {TEST_IMAGE_PATH}")
        return False
    
    # Prepare form data
    data = {
        "username": "testuser_with_pic",
        "email": "testuser_with_pic@example.com",
        "password": "testpassword123",
        "role": "Player",
        "status": 1
    }
    
    # Prepare file upload
    with open(TEST_IMAGE_PATH, 'rb') as f:
        files = {'file': ('profile_pic.png', f, 'image/png')}
        
        response = requests.post(
            f"{BASE_URL}/",
            data=data,
            files=files
        )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ User created successfully with profile picture")
        print(f"User ID: {result.get('_id')}")
        print(f"Profile Photo: {result.get('profile_photo')}")
        return result.get('_id')
    else:
        print(f"❌ Failed to create user: {response.text}")
        return None

def test_update_user_with_profile_pic(user_id):
    """Test updating a user with new profile picture"""
    print(f"\n=== Testing PUT /player/{user_id} with new profile picture ===")
    
    # Check if test image exists
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"❌ Test image not found: {TEST_IMAGE_PATH}")
        return False
    
    # Prepare form data
    data = {
        "username": "updateduser_with_pic",
        "email": "updateduser_with_pic@example.com",
        "role": "Player"
    }
    
    # Prepare file upload
    with open(TEST_IMAGE_PATH, 'rb') as f:
        files = {'file': ('new_profile_pic.png', f, 'image/png')}
        
        response = requests.put(
            f"{BASE_URL}/{user_id}",
            data=data,
            files=files
        )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ User updated successfully with new profile picture")
        print(f"Updated Username: {result.get('username')}")
        print(f"Updated Email: {result.get('email')}")
        print(f"Profile Photo: {result.get('profile_photo')}")
        return True
    else:
        print(f"❌ Failed to update user: {response.text}")
        return False

def test_create_user_without_profile_pic():
    """Test creating a user without profile picture"""
    print("\n=== Testing POST /player/ without profile picture ===")
    
    # Prepare form data
    data = {
        "username": "testuser_no_pic",
        "email": "testuser_no_pic@example.com",
        "password": "testpassword123",
        "role": "Player",
        "status": 1
    }
    
    response = requests.post(
        f"{BASE_URL}/",
        json=data  # Use JSON instead of form data
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ User created successfully without profile picture")
        print(f"User ID: {result.get('_id')}")
        print(f"Profile Photo: {result.get('profile_photo')}")
        return result.get('_id')
    else:
        print(f"❌ Failed to create user: {response.text}")
        return None

def test_update_user_without_profile_pic(user_id):
    """Test updating a user without changing profile picture"""
    print(f"\n=== Testing PUT /player/{user_id} without profile picture ===")
    
    # Prepare form data
    data = {
        "username": "updateduser_no_pic",
        "email": "updateduser_no_pic@example.com",
        "role": "Player"
    }
    
    response = requests.put(
        f"{BASE_URL}/{user_id}",
        json=data  # Use JSON instead of form data
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ User updated successfully without changing profile picture")
        print(f"Updated Username: {result.get('username')}")
        print(f"Updated Email: {result.get('email')}")
        print(f"Profile Photo: {result.get('profile_photo')}")
        return True
    else:
        print(f"❌ Failed to update user: {response.text}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Integrated Profile Picture Upload Functionality")
    print("=" * 60)
    
    # Test 1: Create user with profile picture
    user_id_1 = test_create_user_with_profile_pic()
    
    # Test 2: Update user with new profile picture
    if user_id_1:
        test_update_user_with_profile_pic(user_id_1)
    
    # Test 3: Create user without profile picture
    user_id_2 = test_create_user_without_profile_pic()
    
    # Test 4: Update user without profile picture
    if user_id_2:
        test_update_user_without_profile_pic(user_id_2)
    
    print("\n" + "=" * 60)
    print("🎉 Testing completed!")

if __name__ == "__main__":
    main() 