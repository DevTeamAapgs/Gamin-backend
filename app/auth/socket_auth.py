from typing import Optional, Dict, Any
from fastapi import WebSocket, HTTPException
from app.auth.token_manager import token_manager
from app.models.player import Player
from app.db.mongo import get_database
import logging

logger = logging.getLogger(__name__)

class WebSocketAuthManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def authenticate_websocket(self, websocket: WebSocket, token: str, device_fingerprint: str, ip_address: str) -> Optional[Player]:
        """Authenticate WebSocket connection."""
        try:
            # Verify token
            payload = token_manager.verify_token(token)
            if not payload:
                await websocket.close(code=4001, reason="Invalid token")
                return None
            
            player_id = payload.get("sub")
            if not player_id:
                await websocket.close(code=4001, reason="Invalid token payload")
                return None
            
            # Get database
            db = get_database()
            if not db:
                await websocket.close(code=4002, reason="Database connection error")
                return None
            
            # Get player
            player_data = await db.players.find_one({"_id": player_id})
            if not player_data:
                await websocket.close(code=4003, reason="Player not found")
                return None
            
            player = Player(**player_data)
            
            # Validate session
            token_hash = token_manager._generate_token_seed()  # Simplified for demo
            session = await token_manager.validate_session(token_hash, device_fingerprint, ip_address)
            if not session:
                await websocket.close(code=4004, reason="Invalid session")
                return None
            
            # Store connection
            self.active_connections[player_id] = websocket
            
            logger.info(f"WebSocket authenticated for player {player.username}")
            return player
            
        except Exception as e:
            logger.error(f"WebSocket authentication failed: {e}")
            await websocket.close(code=4000, reason="Authentication failed")
            return None
    
    async def disconnect_player(self, player_id: str):
        """Disconnect player from WebSocket."""
        if player_id in self.active_connections:
            websocket = self.active_connections[player_id]
            await websocket.close()
            del self.active_connections[player_id]
            logger.info(f"Player {player_id} disconnected from WebSocket")
    
    async def send_to_player(self, player_id: str, message: Dict[str, Any]):
        """Send message to specific player."""
        if player_id in self.active_connections:
            websocket = self.active_connections[player_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to player {player_id}: {e}")
                await self.disconnect_player(player_id)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all connected players."""
        disconnected_players = []
        
        for player_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send broadcast to player {player_id}: {e}")
                disconnected_players.append(player_id)
        
        # Clean up disconnected players
        for player_id in disconnected_players:
            await self.disconnect_player(player_id)
    
    def get_connected_players(self) -> list:
        """Get list of connected player IDs."""
        return list(self.active_connections.keys())
    
    def is_player_connected(self, player_id: str) -> bool:
        """Check if player is connected."""
        return player_id in self.active_connections

websocket_auth_manager = WebSocketAuthManager() 