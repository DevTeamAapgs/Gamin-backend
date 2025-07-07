#!/usr/bin/env python3
"""
Test script for prefix generation functionality
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.common.prefix import generate_prefix, get_prefix_info

async def test_prefix_generation():
    """Test the prefix generation functionality"""
    
    print("Testing Prefix Generation Functionality")
    print("=" * 50)
    
    try:
        # Test 1: Generate prefix for Player module with 3 digits
        print("\n1. Testing Player module with 3 digits:")
        player_prefix = await generate_prefix("Player", 3)
        print(f"   Generated prefix: {player_prefix}")
        
        # Test 2: Generate prefix for Player module with 4 digits
        print("\n2. Testing Player module with 4 digits:")
        player_prefix_4 = await generate_prefix("Player", 4)
        print(f"   Generated prefix: {player_prefix_4}")
        
        # Test 3: Generate prefix for Player module with 2 digits
        print("\n3. Testing Player module with 2 digits:")
        player_prefix_2 = await generate_prefix("Player", 2)
        print(f"   Generated prefix: {player_prefix_2}")
        
        # Test 4: Get prefix info without updating
        print("\n4. Getting prefix info for Player module:")
        prefix_info = await get_prefix_info("Player")
        if prefix_info:
            print(f"   Prefix info: {prefix_info}")
        else:
            print("   No prefix info found")
            
        # Test 5: Try with non-existent module
        print("\n5. Testing non-existent module:")
        try:
            non_existent = await generate_prefix("NonExistent", 3)
            print(f"   Generated prefix: {non_existent}")
        except ValueError as e:
            print(f"   Expected error: {e}")
            
    except Exception as e:
        print(f"Error during testing: {e}")

if __name__ == "__main__":
    asyncio.run(test_prefix_generation()) 