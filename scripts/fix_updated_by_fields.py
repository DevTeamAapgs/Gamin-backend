#!/usr/bin/env python3
"""
Script to fix updated_by and created_by fields in the database.
Converts username strings to ObjectIds by looking up the user by username.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.mongo import connect_to_mongo, close_mongo_connection, get_database
from bson import ObjectId
from datetime import datetime

async def fix_updated_by_fields():
    """Fix updated_by and created_by fields to use ObjectIds instead of usernames."""
    await connect_to_mongo()
    
    try:
        db = get_database()
        
        # Find all documents with string values in updated_by or created_by
        players_with_string_audit = await db.players.find({
            "$or": [
                {"updated_by": {"$type": "string"}},
                {"created_by": {"$type": "string"}}
            ]
        }).to_list(length=None)
        
        print(f"Found {len(players_with_string_audit)} players with string audit fields")
        
        if not players_with_string_audit:
            print("No players found with string audit fields")
            return
        
        # Process each player
        for player in players_with_string_audit:
            player_id = player["_id"]
            updates = {}
            
            # Fix updated_by field
            if player.get("updated_by") and isinstance(player["updated_by"], str):
                username = player["updated_by"]
                # Look up user by username
                user_doc = await db.players.find_one({"username": username})
                if user_doc:
                    updates["updated_by"] = user_doc["_id"]
                    print(f"Fixed updated_by for player {player['username']}: {username} -> {user_doc['_id']}")
                else:
                    # If user not found, set to None
                    updates["updated_by"] = None
                    print(f"User not found for updated_by: {username}, setting to None")
            
            # Fix created_by field
            if player.get("created_by") and isinstance(player["created_by"], str):
                username = player["created_by"]
                # Look up user by username
                user_doc = await db.players.find_one({"username": username})
                if user_doc:
                    updates["created_by"] = user_doc["_id"]
                    print(f"Fixed created_by for player {player['username']}: {username} -> {user_doc['_id']}")
                else:
                    # If user not found, set to None
                    updates["created_by"] = None
                    print(f"User not found for created_by: {username}, setting to None")
            
            # Update the player document
            if updates:
                result = await db.players.update_one(
                    {"_id": player_id},
                    {"$set": updates}
                )
                if result.modified_count > 0:
                    print(f"Updated player {player['username']} ({player_id})")
                else:
                    print(f"Failed to update player {player['username']} ({player_id})")
        
        print("Audit field fix completed!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(fix_updated_by_fields()) 