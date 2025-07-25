from typing import Optional, Dict, Any
from fastapi import WebSocket, HTTPException
from app.auth.token_manager import token_manager
from app.models.player import Player
from app.db.mongo import get_database
import logging
from bson import ObjectId
from app.auth.cookie_auth import cookie_auth
from app.utils.crypto_dependencies import get_crypto_service
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
                logger.warning(f"WebSocket close: Invalid token {token}")
                await websocket.close(code=4001, reason="Invalid token")
                return None
            
            player_id = payload.get("sub")
            if not player_id:
                logger.warning(f"WebSocket close: Invalid token payload {payload}")
                await websocket.close(code=4001, reason="Invalid token payload")
                return None
            
            # Get database
            db = get_database()
            if db is None:
                logger.warning("WebSocket close: Database connection error")
                await websocket.close(code=4002, reason="Database connection error")
                return None
            
            # Get player
            player_data = await db.players.find_one({"_id": ObjectId(player_id)})
            
            if not player_data:
                logger.warning(f"WebSocket close: Player not found {player_id}")
                await websocket.close(code=4003, reason="Player not found")
                return None
            
            # Decrypt numeric and gems fields before creating Player
            crypto = get_crypto_service()
            for field in ["token_balance", "total_tokens_earned", "total_tokens_spent"]:
                value = player_data.get(field, "0")
                if isinstance(value, str):
                    try:
                        player_data[field] = float(crypto.decrypt(value))
                    except Exception:
                        player_data[field] = 0.0
                else:
                    player_data[field] = float(value)

            gems_value = player_data.get("gems", {})
            if isinstance(gems_value, dict):
                decrypted_gems = {}
                for color in ["blue", "green", "red"]:
                    val = gems_value.get(color, "0")
                    if isinstance(val, str):
                        try:
                            decrypted_gems[color] = int(crypto.decrypt(val))
                        except Exception:
                            decrypted_gems[color] = 0
                    else:
                        decrypted_gems[color] = int(val)
                player_data["gems"] = decrypted_gems
            else:
                player_data["gems"] = {"blue": 0, "green": 0, "red": 0}

            player = Player(**player_data)
            player.id = str(player_data.get('_id'))  # Ensure player.id is always available
            # Validate session
            token_hash = token_manager._generate_token_seed() 
            # Simplified for demo
            """session = await token_manager.validate_session(token_hash, device_fingerprint, ip_address)
            print(session,"session")
            
            if not session:
                logger.warning(f"WebSocket close: Invalid session for player_id={player_id}, fingerprint={device_fingerprint}, ip={ip_address}")
                await websocket.close(code=4004, reason="Invalid session")
                return None
            """
            # Store connection
            self.active_connections[player_id] = websocket
            
            logger.info(f"WebSocket authenticated for player {player.username}")
            return player
            
        except Exception as e:
            logger.error(f"WebSocket authentication failed: {e}")
            try:
                if websocket.application_state == websocket.application_state.CONNECTED:
                    await websocket.close(code=4000, reason="Authentication failed")
            except Exception:
                pass
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