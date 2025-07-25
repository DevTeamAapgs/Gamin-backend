from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Request
from app.auth.socket_auth import websocket_auth_manager
from app.services.analytics import analytics_service
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.mongo import get_database
from app.auth.cookie_auth import cookie_auth
from typing import Callable
import logging
import json
from app.models.player import Player
from bson import ObjectId
from datetime import datetime
from app.models.game import GemType, GameAttempt
from app.core.enums import GameStatus
from app.utils.crypto_utils import decrypt_player_fields
from app.utils.crypto import AESCipher

logger = logging.getLogger(__name__)
router = APIRouter()

# Store initial device info for fraud check
player_device_info = {}

# Store active player sessions
player_game_sessions = {}  # player_id: ObjectId of game_socket


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    device_fingerprint: str = Query(...),
    ip_address: str = Query(...)
):
    """WebSocket endpoint for real-time game communication."""
    await websocket.accept()
    try:
        token = cookie_auth.get_token_from_websocket(websocket)
        print(token, "token")

        # Authenticate WebSocket connection
        player = await websocket_auth_manager.authenticate_websocket(
            websocket, token, device_fingerprint, ip_address
        )
        if not player:
            if websocket.application_state == websocket.application_state.CONNECTED:
                await websocket.close(code=4001, reason="Authentication failed")
            return
        
        logger.info(f"WebSocket connected for player: {player.username}")
        if websocket.application_state == websocket.application_state.CONNECTED:
            await websocket.send_json({
                "type": "connection_established",
                "player_id": str(player.id),
                "username": player.username,
                "message": "Connected to gaming platform"
            })
        else:
            return
        
        try:
            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    await process_websocket_message(websocket, player, message)
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected for player: {player.username}")
                    await websocket_auth_manager.disconnect_player(str(player.id))
                    return
                except json.JSONDecodeError:
                    if websocket.application_state == websocket.application_state.CONNECTED:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Invalid JSON format"
                        })
                    return
        except Exception as e:
            logger.error(f"WebSocket error for player {player.username}: {e}")
            if websocket.application_state == websocket.application_state.CONNECTED:
                await websocket.send_json({
                    "type": "error",
                    "message": "Internal server error"
                })
            return
        finally:
            # Finalize game session and reward on disconnect
            game_attempt_id = player_game_sessions.pop(str(player.id), None)
            if game_attempt_id:
                db = get_database()
                end_time = datetime.utcnow()
                game_attempt = await db.game_socket.find_one({"_id": ObjectId(game_attempt_id)})

                if game_attempt:
                    start_time = game_attempt.get("start_time", end_time)
                    duration = (end_time - start_time).total_seconds()
                    score = game_attempt.get("score", 0)
                    entry_cost = game_attempt.get("entry_cost", 0)
                    token_balance = game_attempt.get("token_balance", 0)
                    gems_spent = game_attempt.get("gems_spent", {"blue": 0, "green": 0, "red": 0})
                    game_type = game_attempt.get("game_type", "main")

                    # Calculate rewards
                    tokens_earned = round((entry_cost + token_balance) * (score / 100), 2)
                    gems_earned = (
                        {k: int(v * (score / 100)) for k, v in gems_spent.items()}
                        if game_type == "main" else {"blue": 0, "green": 0, "red": 0}
                    )

                    await db.game_socket.update_one(
                        {"_id": ObjectId(game_attempt_id)},
                        {
                            "$set": {
                                "game_status": GameStatus.INACTIVE.value,
                                "end_time": end_time,
                                "duration": duration,
                                "tokens_earned": tokens_earned,
                                "gems_earned": gems_earned
                            }
                        }
                    )

                    # Return rewards to player
                    update = {"$inc": {"token_balance": tokens_earned}}
                    if game_type == "main":
                        update["$inc"].update({
                            f"gems.{k}": gems_earned[k] for k in gems_earned
                        })

                    await db.players.update_one({"_id": ObjectId(player.id)}, update)
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            if websocket.application_state == websocket.application_state.CONNECTED:
                await websocket.close(code=4000, reason="Connection error")
        except Exception:
            pass


async def handle_join_game(websocket, player, message):
    db = get_database()
    try:
        game_level_id = ObjectId(message["game_level_id"])
        game_type = message["game_type"]  # "main" or "quest"
        device_fingerprint = message.get("device_fingerprint", player.device_fingerprint)
        ip_address = message.get("ip_address", player.ip_address)

        player_id_str = str(player.id)

        # Fraud check
        if player_id_str not in player_device_info:
            player_device_info[player_id_str] = {
                "device_fingerprint": device_fingerprint,
                "ip_address": ip_address
            }
        else:
            info = player_device_info[player_id_str]
            if info["device_fingerprint"] != device_fingerprint or info["ip_address"] != ip_address:
                await websocket.send_json({
                    "type": "fraud",
                    "message": "Device/IP mismatch detected. Connection closed."
                })
                await websocket.close(code=4005, reason="Fraud detected")
                return

        # Fetch game level config
        game_level = await db.game_level_configuration.find_one({"_id": game_level_id})
        if not game_level:
            await websocket.send_json({"type": "error", "message": "Invalid game level"})
            return

        fk_game_configuration_id = game_level["fk_game_configuration_id"]
        level_number = game_level["level_number"]
        entry_cost = game_level["entry_cost"]
        entry_cost_gems = game_level.get("entry_cost_gems", {"blue": 0, "green": 0, "red": 0})

        # Decrypt entry_cost and entry_cost_gems if they are strings (encrypted)
        crypto = AESCipher()
        try:
            if isinstance(entry_cost, str):
                entry_cost = float(crypto.decrypt(entry_cost))
        except Exception:
            entry_cost = 0.0
        try:
            if isinstance(entry_cost_gems, str):
                entry_cost_gems = json.loads(crypto.decrypt(entry_cost_gems))
            elif isinstance(entry_cost_gems, dict):
                # Decrypt each color if needed
                for color in ["blue", "green", "red"]:
                    if isinstance(entry_cost_gems.get(color), str):
                        entry_cost_gems[color] = int(float(crypto.decrypt(entry_cost_gems[color])))
        except Exception:
            entry_cost_gems = {"blue": 0, "green": 0, "red": 0}

        # Get latest player doc
        player_doc = await db.players.find_one({"_id": ObjectId(player.id)})
        if not player_doc:
            await websocket.send_json({"type": "error", "message": "Player not found"})
            return

        player_doc = decrypt_player_fields(player_doc)
        token_balance = player_doc.get("token_balance", 0)
        gems = player_doc.get("gems", {"blue": 0, "green": 0, "red": 0})
        if isinstance(gems, GemType):
            gems = {"blue": gems.blue, "green": gems.green, "red": gems.red}

        # --- Ensure all values are numbers ---
        try:
            token_balance = float(token_balance)
        except Exception:
            token_balance = 0.0
        try:
            entry_cost = float(entry_cost)
        except Exception:
            entry_cost = 0.0
        # Convert all values in gems and entry_cost_gems to int
        gems = {k: int(float(v)) for k, v in gems.items()}
        entry_cost_gems = {k: int(float(v)) for k, v in entry_cost_gems.items()}
        # Debug print types
        print("token_balance:", token_balance, type(token_balance))
        print("entry_cost:", entry_cost, type(entry_cost))
        print("gems:", gems, {k: type(v) for k, v in gems.items()})
        print("entry_cost_gems:", entry_cost_gems, {k: type(v) for k, v in entry_cost_gems.items()})
        # --- End ensure numbers ---

        # Entry cost validation
        if game_type == "main":
            if token_balance < entry_cost or any(
                gems.get(color, 0) < entry_cost_gems.get(color, 0)
                for color in ["blue", "green", "red"]
            ):
                await websocket.send_json({"type": "error", "message": "Insufficient tokens or gems"})
                return
        elif game_type == "quest":
            if token_balance < entry_cost:
                await websocket.send_json({"type": "error", "message": "Insufficient tokens"})
                return

        # Deduct entry cost
        update_fields = {"token_balance": token_balance - entry_cost}
        if game_type == "main":
            update_fields["gems"] = {
                color: gems.get(color, 0) - entry_cost_gems.get(color, 0)
                for color in ["blue", "green", "red"]
            }

        await db.players.update_one({"_id": ObjectId(player.id)}, {"$set": update_fields})

        # Create GameAttempt
        game_attempt = {
            "fk_player_id": ObjectId(player.id),
            "fk_game_configuration_id": fk_game_configuration_id,
            "fk_game_level_id": game_level_id,
            "ip_address": ip_address,
            "device_fingerprint": device_fingerprint,
            "level_number": level_number,
            "game_status": GameStatus.ACTIVE.value,
            "score": 0,
            "tokens_earned": 0.0,
            "gems_earned": {"blue": 0, "green": 0, "red": 0},
            "entry_cost": entry_cost,
            "gems_spent": entry_cost_gems if game_type == "main" else {"blue": 0, "green": 0, "red": 0},
            "start_time": datetime.utcnow(),
            "end_time": None,
            "duration": None,
            "moves_count": 0,
            "max_moves": 100,
            "game_data": {},
            "replay_data": [],
            "completion_percentage": 0.0,
        }

        result = await db.game_socket.insert_one(game_attempt)
        game_attempt_id = result.inserted_id
        player_game_sessions[str(player.id)] = game_attempt_id

        await websocket.send_json({
            "type": "game_joined",
            "game_attempt_id": str(game_attempt_id),
            "message": "Game joined successfully"
        })

    except Exception as e:
        await websocket.send_json({"type": "error", "message": f"Join game failed: {str(e)}"})
        return


async def process_websocket_message(websocket: WebSocket, player, message: dict):
    message_type = message.get("type")
    db = get_database()

    if message_type == "join_game":
        await handle_join_game(websocket, player, message)
    
    elif message_type == "ping":
        await websocket.send_json({
            "type": "pong",
            "timestamp": message.get("timestamp")
        })
    
    elif message_type == "game_action":
        game_attempt_id = player_game_sessions.get(str(player.id))
        if not game_attempt_id:
            await websocket.send_json({"type": "error", "message": "No active game session"})
            return

        await db.game_socket.update_one(
            {"_id": ObjectId(game_attempt_id)},
            {"$inc": {"moves_count": 1}}
        )

        await websocket.send_json({
            "type": "action_confirmed",
            "game_attempt_id": str(game_attempt_id),
            "timestamp": message.get("timestamp")
        })
    
    elif message_type == "game_state_update":
        game_attempt_id = player_game_sessions.get(str(player.id))
        if not game_attempt_id:
            await websocket.send_json({"type": "error", "message": "No active game session"})
            return

        await websocket.send_json({
            "type": "state_updated",
            "game_attempt_id": str(game_attempt_id),
            "timestamp": message.get("timestamp")
        })
    
    elif message_type == "chat_message":
        chat_data = message.get("chat_data", {})
        await websocket_auth_manager.broadcast_to_all({
            "type": "chat_message",
            "player_id": str(player.id),
            "username": player.username,
            "message": chat_data.get("message"),
            "timestamp": message.get("timestamp")
        })
    
    elif message_type == "exit_game":
        # Finalize session and update DB as on disconnect
        game_attempt_id = player_game_sessions.pop(str(player.id), None)
        if game_attempt_id:
            end_time = datetime.utcnow()
            game_attempt = await db.game_socket.find_one({"_id": ObjectId(game_attempt_id)})
            if game_attempt:
                start_time = game_attempt.get("start_time", end_time)
                duration = (end_time - start_time).total_seconds()
                score = game_attempt.get("score", 0)
                entry_cost = game_attempt.get("entry_cost", 0)
                token_balance = game_attempt.get("token_balance", 0)
                gems_spent = game_attempt.get("gems_spent", {"blue": 0, "green": 0, "red": 0})
                game_type = game_attempt.get("game_type", "main")

                # Calculate rewards
                tokens_earned = round((entry_cost + token_balance) * (score / 100), 2)
                gems_earned = (
                    {k: int(v * (score / 100)) for k, v in gems_spent.items()}
                    if game_type == "main" else {"blue": 0, "green": 0, "red": 0}
                )

                await db.game_socket.update_one(
                    {"_id": ObjectId(game_attempt_id)},
                    {
                        "$set": {
                            "game_status": GameStatus.INACTIVE.value,
                            "end_time": end_time,
                            "duration": duration,
                            "tokens_earned": tokens_earned,
                            "gems_earned": gems_earned
                        }
                    }
                )

                # Return rewards to player
                update = {"$inc": {"token_balance": tokens_earned}}
                if game_type == "main":
                    update["$inc"].update({
                        f"gems.{k}": gems_earned[k] for k in gems_earned
                    })
                await db.players.update_one({"_id": ObjectId(player.id)}, update)
        await websocket.send_json({"type": "game_exited", "message": "You have exited the game."})
        await websocket.close()
    
    else:
        await websocket.send_json({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        })


@router.get("/status")
async def get_websocket_status(request: Request):
    """Get WebSocket connection status."""
    connected_players = websocket_auth_manager.get_connected_players()
    return {
        "connected_players": len(connected_players),
        "active_connections": connected_players
    }
