#!/usr/bin/env python3
"""
Script to update existing admins with generated admin_prefix values.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.mongo import connect_to_mongo, close_mongo_connection
from app.utils.prefix import generate_prefix
from datetime import datetime

async def update_existing_admin_prefixes():
    """Update existing admins with generated admin_prefix values."""
    await connect_to_mongo()
    
    try:
        from app.db.mongo import get_database
        db = get_database()
        
        # Find all admins without admin_prefix
        admins_without_prefix = await db.players.find({
            "playertype": 1,
            "$or": [
                {"admin_prefix": {"$exists": False}},
                {"admin_prefix": None}
            ]
        }).to_list(length=None)
        
        print(f"Found {len(admins_without_prefix)} admins without admin_prefix")
        
        if not admins_without_prefix:
            print("All admins already have admin_prefix values")
            return
        
        # Update each admin with a generated prefix
        for admin in admins_without_prefix:
            try:
                # Generate admin prefix
                admin_prefix = await generate_prefix("admin", 4)
                
                # Update the admin document
                result = await db.players.update_one(
                    {"_id": admin["_id"]},
                    {
                        "$set": {
                            "admin_prefix": admin_prefix,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                if result.modified_count > 0:
                    print(f"Updated admin {admin['username']} with prefix: {admin_prefix}")
                else:
                    print(f"Failed to update admin {admin['username']}")
                    
            except Exception as e:
                print(f"Error updating admin {admin['username']}: {e}")
        
        print("Admin prefix update completed!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(update_existing_admin_prefixes()) 