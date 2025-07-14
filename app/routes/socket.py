from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Request, Depends
from app.auth.socket_auth import websocket_auth_manager
from app.services.analytics import analytics_service

from typing import Callable
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    device_fingerprint: str = Query(...),
    ip_address: str = Query(...)
):
    """WebSocket endpoint for real-time game communication."""
    await websocket.accept()
    
    try:
        # Authenticate WebSocket connection
        player = await websocket_auth_manager.authenticate_websocket(
            websocket, token, device_fingerprint, ip_address
        )
        
        if not player:
            await websocket.close(code=4001, reason="Authentication failed")
            return
        
        logger.info(f"WebSocket connected for player: {player.username}")
        
        # Send welcome message
        await websocket.send_json({
            "type": "connection_established",
            "player_id": str(player.id),
            "username": player.username,
            "message": "Connected to gaming platform"
        })
        
        # Handle incoming messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Process message based on type
                await process_websocket_message(websocket, player, message)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for player: {player.username}")
                await websocket_auth_manager.disconnect_player(str(player.id))
                break
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
                
            except Exception as e:
                logger.error(f"WebSocket error for player {player.username}: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Internal server error"
                })
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket.close(code=4000, reason="Connection error")

async def process_websocket_message(websocket: WebSocket, player, message: dict):
    """Process incoming WebSocket messages."""
    message_type = message.get("type")
    
    if message_type == "ping":
        # Handle ping/pong for connection health
        await websocket.send_json({
            "type": "pong",
            "timestamp": message.get("timestamp")
        })
    
    elif message_type == "game_action":
        # Track game action for analytics
        game_id = message.get("game_id")
        action_data = message.get("action_data", {})
        
        if game_id:
            await analytics_service.track_game_action(
                game_id, str(player.id), action_data
            )
        
        # Broadcast to other players if needed
        await websocket.send_json({
            "type": "action_confirmed",
            "game_id": game_id,
            "timestamp": message.get("timestamp")
        })
    
    elif message_type == "game_state_update":
        # Handle game state updates
        game_id = message.get("game_id")
        state_data = message.get("state_data", {})
        
        # Process game state update
        await websocket.send_json({
            "type": "state_updated",
            "game_id": game_id,
            "timestamp": message.get("timestamp")
        })
    
    elif message_type == "chat_message":
        # Handle chat messages (if implemented)
        chat_data = message.get("chat_data", {})
        
        # Broadcast chat message to other players
        await websocket_auth_manager.broadcast_to_all({
            "type": "chat_message",
            "player_id": str(player.id),
            "username": player.username,
            "message": chat_data.get("message"),
            "timestamp": message.get("timestamp")
        })
    
    else:
        # Unknown message type
        await websocket.send_json({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        })

@router.get("/status")
async def get_websocket_status(request: Request):
    """Get WebSocket connection status."""
    connected_players = websocket_auth_manager.get_connected_players()
    
    response_data = {
        "connected_players": len(connected_players),
        "active_connections": connected_players
    }
    return response_data