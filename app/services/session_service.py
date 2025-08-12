from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from bson import ObjectId
from app.db.mongo import get_database
from app.models.game import GameSession
import logging

logger = logging.getLogger(__name__)

class SessionService:
    """Service for managing persistent socket sessions"""
    
    def __init__(self):
        self.db = get_database()
    
    async def get_active_session(self, sid: str) -> Optional[Dict[str, Any]]:
        """
        Get active session information by socket ID
        
        Args:
            sid: Socket.IO session ID
            
        Returns:
            Session data dict or None if not found
        """
        try:
            session_doc = await self.db.game_sessions_socket_details.find_one({
                "socket_id": sid,
                "status": {"$in": ["CONNECTED", "IN_GAME"]}
            })
            
            if session_doc:
                # Update last_seen timestamp
                await self.db.game_sessions_socket_details.update_one(
                    {"_id": session_doc["_id"]},
                    {"$set": {"last_seen": datetime.utcnow()}}
                )
                
            return session_doc
        except Exception as e:
            logger.error(f"Error getting active session for sid {sid}: {e}")
            return None
    
    async def create_or_update_session(
        self, 
        player_id: ObjectId, 
        sid: str, 
        ip_address: str = None, 
        device_fingerprint: str = None
    ) -> bool:
        """
        Create new session or update existing one for player
        
        Args:
            player_id: Player ObjectId
            sid: Socket.IO session ID
            ip_address: Client IP address
            device_fingerprint: Device fingerprint
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if session already exists for this player
            existing_session = await self.db.game_sessions_socket_details.find_one({
                "player_id": player_id,
                "status": {"$in": ["CONNECTED", "IN_GAME"]}
            })
            
            session_data = {
                "player_id": player_id,
                "socket_id": sid,
                "ip_address": ip_address,
                "device_fingerprint": device_fingerprint,
                "last_seen": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            print("session_datasssssssssssssssssss",session_data)
            if existing_session:
                # Update existing session
                await self.db.game_sessions_socket_details.update_one(
                    {"_id": existing_session["_id"]},
                    {"$set": session_data}
                )
                logger.info(f"Updated existing session for player {player_id} with sid {sid}")
            else:
                # Create new session
                session_data.update({
                    "status": "CONNECTED",
                    "created_at": datetime.utcnow()
                })
                await self.db.game_sessions_socket_details.insert_one(session_data)
                logger.info(f"Created new session for player {player_id} with sid {sid}")
            
            return True
        except Exception as e:
            logger.error(f"Error creating/updating session for player {player_id}: {e}")
            return False
    
    async def disconnect_session(self, sid: str) -> bool:
        """
        Mark session as disconnected
        
        Args:
            sid: Socket.IO session ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.db.game_sessions_socket_details.update_one(
                {"socket_id": sid},
                {
                    "$set": {
                        "status": "DISCONNECTED",
                        "last_seen": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Marked session {sid} as disconnected")
                return True
            else:
                logger.warning(f"No session found to disconnect for sid {sid}")
                return False
        except Exception as e:
            logger.error(f"Error disconnecting session {sid}: {e}")
            return False
    
    async def update_game_attempt_id(self, sid: str, game_attempt_id: ObjectId) -> bool:
        """
        Update session with current game attempt ID
        
        Args:
            sid: Socket.IO session ID
            game_attempt_id: Game attempt ObjectId
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.db.game_sessions_socket_details.update_one(
                {"socket_id": sid},
                {
                    "$set": {
                        "game_attempt_id": game_attempt_id,
                        "status": "IN_GAME",
                        "last_seen": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated session {sid} with game_attempt_id {game_attempt_id}")
                return True
            else:
                logger.warning(f"No session found to update for sid {sid}")
                return False
        except Exception as e:
            logger.error(f"Error updating game_attempt_id for session {sid}: {e}")
            return False
    
    async def clear_game_attempt_id(self, sid: str) -> bool:
        """
        Clear game attempt ID from session (when game ends)
        
        Args:
            sid: Socket.IO session ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.db.game_sessions_socket_details.update_one(
                {"socket_id": sid},
                {
                    "$set": {
                        "game_attempt_id": None,
                        "status": "CONNECTED",
                        "last_seen": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Cleared game_attempt_id from session {sid}")
                return True
            else:
                logger.warning(f"No session found to clear game_attempt_id for sid {sid}")
                return False
        except Exception as e:
            logger.error(f"Error clearing game_attempt_id for session {sid}: {e}")
            return False
    
    async def cleanup_stale_sessions(self, hours: int = 24) -> int:
        """
        Clean up sessions that haven't been seen for specified hours
        
        Args:
            hours: Number of hours to consider session stale
            
        Returns:
            Number of sessions cleaned up
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            result = await self.db.game_sessions_socket_details.delete_many({
                "last_seen": {"$lt": cutoff_time},
                "status": "DISCONNECTED"
            })
            
            logger.info(f"Cleaned up {result.deleted_count} stale sessions")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up stale sessions: {e}")
            return 0
    
    async def get_player_session(self, player_id: ObjectId) -> Optional[Dict[str, Any]]:
        """
        Get active session for a specific player
        
        Args:
            player_id: Player ObjectId
            
        Returns:
            Session data dict or None if not found
        """
        try:
            session_doc = await self.db.game_sessions_socket_details.find_one({
                "player_id": player_id,
                "status": {"$in": ["CONNECTED", "IN_GAME"]}
            })
            return session_doc
        except Exception as e:
            logger.error(f"Error getting player session for {player_id}: {e}")
            return None

# Global instance
session_service = SessionService() 