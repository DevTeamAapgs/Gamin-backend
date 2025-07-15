import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

import motor.motor_asyncio
from app.core.config import settings
from app.core.enums import PlayerType
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_database():
    """Initialize database with collections and indexes."""
    try:
        # Connect to MongoDB
        client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.mongodb_db_name]
        
        logger.info("Connected to MongoDB")
        
        # Create collections if they don't exist
        collections = [
            "players",
            "games", 
            "transactions",
            "game_levels",
            "request_logs",
            "security_logs", 
            "game_action_logs"
        ]
        
        for collection_name in collections:
            if collection_name not in await db.list_collection_names():
                await db.create_collection(collection_name)
                logger.info(f"Created collection: {collection_name}")
        
        # Create indexes for players collection
        await db.players.create_index("username", unique=True)
        await db.players.create_index("email", unique=True)
        await db.players.create_index("wallet_address", unique=True)
        await db.players.create_index("created_at")
        await db.players.create_index("last_login")
        logger.info("Created indexes for players collection")
        
        # Create indexes for games collection
        await db.games.create_index("player_id")
        await db.games.create_index("game_type")
        await db.games.create_index("status")
        await db.games.create_index("created_at")
        await db.games.create_index("completed_at")
        logger.info("Created indexes for games collection")
        
        # Create indexes for transactions collection
        await db.transactions.create_index("player_id")
        await db.transactions.create_index("transaction_type")
        await db.transactions.create_index("status")
        await db.transactions.create_index("created_at")
        await db.transactions.create_index("tx_hash", unique=True)
        logger.info("Created indexes for transactions collection")
        
        # Create indexes for game_levels collection
        await db.game_levels.create_index("level_number", unique=True)
        await db.game_levels.create_index("difficulty")
        logger.info("Created indexes for game_levels collection")
        
        # Create indexes for request_logs collection
        await db.request_logs.create_index("player_id")
        await db.request_logs.create_index("method")
        await db.request_logs.create_index("path")
        await db.request_logs.create_index("status_code")
        await db.request_logs.create_index("client_ip")
        await db.request_logs.create_index("created_at")
        await db.request_logs.create_index("ttl", expireAfterSeconds=0)  # TTL index
        logger.info("Created indexes for request_logs collection")
        
        # Create indexes for security_logs collection
        await db.security_logs.create_index("player_id")
        await db.security_logs.create_index("event_type")
        await db.security_logs.create_index("severity")
        await db.security_logs.create_index("client_ip")
        await db.security_logs.create_index("created_at")
        await db.security_logs.create_index("ttl", expireAfterSeconds=0)  # TTL index
        logger.info("Created indexes for security_logs collection")
        
        # Create indexes for game_action_logs collection
        await db.game_action_logs.create_index("game_id")
        await db.game_action_logs.create_index("player_id")
        await db.game_action_logs.create_index("action_type")
        await db.game_action_logs.create_index("session_id")
        await db.game_action_logs.create_index("timestamp")
        logger.info("Created indexes for game_action_logs collection")
        
        # Insert default game levels if they don't exist
        existing_levels = await db.game_levels.count_documents({})
        if existing_levels == 0:
            default_levels = [
                {
                    "level_number": 1,
                    "difficulty": "easy",
                    "tube_count": 3,
                    "color_count": 3,
                    "time_limit": 60,
                    "reward_tokens": 10,
                    "created_at": datetime.utcnow()
                },
                {
                    "level_number": 2,
                    "difficulty": "easy",
                    "tube_count": 4,
                    "color_count": 4,
                    "time_limit": 75,
                    "reward_tokens": 15,
                    "created_at": datetime.utcnow()
                },
                {
                    "level_number": 3,
                    "difficulty": "medium",
                    "tube_count": 5,
                    "color_count": 5,
                    "time_limit": 90,
                    "reward_tokens": 25,
                    "created_at": datetime.utcnow()
                },
                {
                    "level_number": 4,
                    "difficulty": "medium",
                    "tube_count": 6,
                    "color_count": 6,
                    "time_limit": 120,
                    "reward_tokens": 40,
                    "created_at": datetime.utcnow()
                },
                {
                    "level_number": 5,
                    "difficulty": "hard",
                    "tube_count": 7,
                    "color_count": 7,
                    "time_limit": 150,
                    "reward_tokens": 60,
                    "created_at": datetime.utcnow()
                }
            ]
            
            await db.game_levels.insert_many(default_levels)
            logger.info("Inserted default game levels")
        
        # Create admin user if it doesn't exist
        admin_exists = await db.players.find_one({"username": "admin"})
        if not admin_exists:
            admin_user = {
                "username": "admin",
                "email": "admin@gamingplatform.com",
                "wallet_address": "0x0000000000000000000000000000000000000000",
                "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8eG",  # "admin123"
                "playertype": PlayerType.SUPERADMIN,
                "is_verified": True,
                "token_balance": 0,
                "total_games_played": 0,
                "total_tokens_earned": 0,
                "created_at": datetime.utcnow(),
                "last_login": datetime.utcnow()
            }
            
            await db.players.insert_one(admin_user)
            logger.info("Created admin user (username: admin, password: admin123)")
        
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(init_database()) 