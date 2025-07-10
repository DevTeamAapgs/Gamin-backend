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
        
        # Drop existing indexes to avoid conflicts
        try:
            await db.roles.drop_indexes()
            logger.info("Dropped existing indexes")
        except Exception as e:
            logger.info(f"No existing indexes to drop: {e}")
        
        # Clean up existing data with old structure
        old_roles = await db.roles.find({"role": {"$exists": True}}).to_list(length=10)
        if old_roles:
            logger.info(f"Found {len(old_roles)} old role documents, removing them")
            await db.roles.delete_many({"role": {"$exists": True}})
        
        # Create new index for roles collection
        await db.roles.create_index("role_name", unique=True)
        logger.info("Created index for roles collection")
        
        # Check existing roles
        all_roles = await db.roles.find({}).to_list(length=10)
        logger.info(f"Total roles in database: {len(all_roles)}")
        
        # List existing roles
        for role in all_roles:
            role_name = role.get('role_name', 'Unknown')
            description = role.get('description', 'No description')
            logger.info(f"  - {role_name}: {description}")
        
        # Define specific roles for the system
        specific_roles = [
                {
                "role_name": "admin",
                    "description": "Administrator with full access",
                    "permissions": ["read", "write", "delete", "admin"],
                "created_at": datetime.utcnow(),
                "status": 1,
                "dels": 0
            },
            {
                "role_name": "manager",
                "description": "Manager with limited admin access",
                "permissions": ["read", "write", "moderate"],
                "created_at": datetime.utcnow(),
                "status": 1,
                "dels": 0
                },
                {
                "role_name": "player",
                    "description": "Regular player with game access",
                    "permissions": ["read", "play"],
                "created_at": datetime.utcnow(),
                "status": 1,
                "dels": 0
                },
                {
                "role_name": "superadmin",
                "description": "Super Administrator with highest privileges",
                "permissions": ["read", "write", "delete", "admin", "super"],
                "created_at": datetime.utcnow(),
                "status": 1,
                "dels": 0
            }
        ]
        
        # Check if specific roles exist and create missing ones
        roles_to_check = ["admin", "manager", "player", "superadmin"]
        missing_roles = []
        
            for role_name in roles_to_check:
            role_exists = await db.roles.find_one({"role_name": role_name})
                if not role_exists:
                missing_roles.append(role_name)
                    logger.warning(f"Role '{role_name}' not found in database")
                else:
                    logger.info(f"Role '{role_name}' exists")
        
        # Insert missing roles
        if missing_roles:
            roles_to_insert = [role for role in specific_roles if role["role_name"] in missing_roles]
            
            if roles_to_insert:
                await db.roles.insert_many(roles_to_insert)
                logger.info(f"Inserted missing roles: {[role['role_name'] for role in roles_to_insert]}")
        
        # Final check
        final_roles = await db.roles.find({}).to_list(length=10)
        logger.info(f"Final roles in database: {len(final_roles)}")
        for role in final_roles:
            role_name = role.get('role_name', 'Unknown')
            description = role.get('description', 'No description')
            logger.info(f"  - {role_name}: {description}")
        
        logger.info("Roles initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Roles initialization failed: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(init_roles()) 