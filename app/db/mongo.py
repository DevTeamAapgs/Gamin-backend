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
        
        # Game session socket details indexes
        # Get existing indexes
        existing_indexes = await db.database.game_sessions_socket_details.index_information()

        # Ensure player_id index
        await db.database.game_sessions_socket_details.create_index("player_id")

        # Ensure socket_id index with unique constraint
        await db.database.game_sessions_socket_details.create_index("socket_id", unique=True)

        # Ensure status index
        await db.database.game_sessions_socket_details.create_index("status")

        # Ensure game_attempt_id index
        await db.database.game_sessions_socket_details.create_index("game_attempt_id")

        # TTL Index for last_seen: 86400 seconds = 24 hours
        if "last_seen_1" in existing_indexes:
            options = existing_indexes["last_seen_1"]
            if "expireAfterSeconds" not in options or options["expireAfterSeconds"] != 86400:
                print("⚠️ TTL index exists with incorrect or missing options. Recreating...")
                await db.database.game_sessions_socket_details.drop_index("last_seen_1")
                await db.database.game_sessions_socket_details.create_index("last_seen", expireAfterSeconds=86400)
            else:
                print("✅ TTL index on 'last_seen' already correctly configured.")
        else:
            await db.database.game_sessions_socket_details.create_index("last_seen", expireAfterSeconds=86400)
            print("✅ TTL index on 'last_seen' created.")

        print("✅ All indexes ensured.")
        
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