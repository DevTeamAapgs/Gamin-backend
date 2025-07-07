#!/usr/bin/env python3
"""
Roles Initialization Script
Creates initial roles for the application
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
import motor.motor_asyncio

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_roles():
    """Initialize roles collection with default roles."""
    try:
        # Connect to MongoDB
        client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.mongodb_db_name]
        
        logger.info("Connected to MongoDB")
        
        # Create roles collection if it doesn't exist
        if "roles" not in await db.list_collection_names():
            await db.create_collection("roles")
            logger.info("Created roles collection")
        
        # Create index for roles collection
        await db.roles.create_index("role", unique=True)
        logger.info("Created index for roles collection")
        
        # Insert default roles if they don't exist
        existing_roles = await db.roles.count_documents({})
        if existing_roles == 0:
            default_roles = [
                {
                    "role": "admin",
                    "description": "Administrator with full access",
                    "permissions": ["read", "write", "delete", "admin"],
                    "created_at": datetime.utcnow()
                },
                {
                    "role": "player",
                    "description": "Regular player with game access",
                    "permissions": ["read", "play"],
                    "created_at": datetime.utcnow()
                },
                {
                    "role": "moderator",
                    "description": "Moderator with limited admin access",
                    "permissions": ["read", "write", "moderate"],
                    "created_at": datetime.utcnow()
                }
            ]
            
            await db.roles.insert_many(default_roles)
            logger.info("Inserted default roles: admin, player, moderator")
        else:
            # Check if specific roles exist
            roles_to_check = ["admin", "player", "moderator"]
            for role_name in roles_to_check:
                role_exists = await db.roles.find_one({"role": role_name})
                if not role_exists:
                    logger.warning(f"Role '{role_name}' not found in database")
                else:
                    logger.info(f"Role '{role_name}' exists")
        
        # List all existing roles
        all_roles = await db.roles.find({}).to_list(length=10)
        logger.info(f"Total roles in database: {len(all_roles)}")
        for role in all_roles:
            logger.info(f"  - {role['role']}: {role.get('description', 'No description')}")
        
        logger.info("Roles initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Roles initialization failed: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(init_roles()) 