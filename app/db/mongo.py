from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

db = Database()

async def connect_to_mongo():
    """Create database connection."""
    try:
        db.client = AsyncIOMotorClient(settings.mongodb_url)
        db.database = db.client.gaming_platform
        logger.info("Connected to MongoDB")
        
        # Create indexes for better performance
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    """Close database connection."""
    if db.client:
        db.client.close()
        logger.info("Disconnected from MongoDB")

async def create_indexes():
    """Create database indexes for optimal performance."""
    try:
        if db.database is None:
            raise Exception("Database not connected")
            
        # Player indexes
        ## await db.database.players.create_index("wallet_address", unique=True)
        await db.database.players.create_index("username", unique=True)
        await db.database.players.create_index("created_at")
        
        # Game indexes
        await db.database.games.create_index("player_id")
        await db.database.games.create_index("game_type")
        await db.database.games.create_index("created_at")
        await db.database.games.create_index("status")
        
        # Session indexes
        await db.database.sessions.create_index("player_id")
        await db.database.sessions.create_index("token_hash")
        await db.database.sessions.create_index("expires_at")
        
        # Transaction indexes
        await db.database.transactions.create_index("player_id")
        await db.database.transactions.create_index("transaction_type")
        await db.database.transactions.create_index("created_at")
        
        # Replay indexes
        await db.database.replays.create_index("game_id")
        await db.database.replays.create_index("player_id")
        await db.database.replays.create_index("created_at")
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")
        raise e

def get_database() :
    """Get database instance."""
    return db.database 