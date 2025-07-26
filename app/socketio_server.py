import socketio
from fastapi import FastAPI
from app.db.mongo import get_database, connect_to_mongo
from app.auth.cookie_auth import cookie_auth
from app.utils.crypto_utils import decrypt_player_fields
from app.models.game import GemType, GameAttempt
from app.core.enums import GameStatus,PlayerTransactionStatus,PlayerTransactionType,GameActionType
from bson import ObjectId
from datetime import datetime
import logging

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

logger = logging.getLogger(__name__)

# Store active player sessions
player_game_sessions = {}  # player_id: ObjectId of game_attempt

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    db = get_database()
    try:
        await db.command("ping")
        logger.info("✅ MongoDB connection established!")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        import sys
        sys.exit(1)

# --- Connection Events ---

@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")
    # Optionally, clean up player_game_sessions here

# --- Game Events ---

@sio.event
async def join_game(sid, data):
    db = get_database()
    try:
        player_id = data.get("player_id")
        game_level_id = ObjectId(data["game_level_id"])
        game_type = data["game_type"]
        device_fingerprint = data.get("device_fingerprint")
        ip_address = data.get("ip_address")

        # Fetch player and game level
        player_doc = await db.players.find_one({"_id": ObjectId(player_id)})
        if not player_doc:
            await sio.emit("error", {"message": "Player not found"}, to=sid)
            return
        player_doc = decrypt_player_fields(player_doc)

        game_level = await db.game_level_configuration.find_one({"_id": game_level_id})
        if not game_level:
            await sio.emit("error", {"message": "Invalid game level"}, to=sid)
            return
        
        logger.info(f"Game level config: {game_level}")

        entry_cost = game_level["entry_cost"]
        entry_cost_gems = game_level.get("entry_cost_gems", {"blue": 0, "green": 0, "red": 0})
        
        # Handle entry_cost_gems if it's a GemType object
        if isinstance(entry_cost_gems, GemType):
            entry_cost_gems = {"blue": entry_cost_gems.blue, "green": entry_cost_gems.green, "red": entry_cost_gems.red}
        
        token_balance = player_doc.get("token_balance", 0)
        gems = player_doc.get("gems", {"blue": 0, "green": 0, "red": 0})
        if isinstance(gems, GemType):
            gems = {"blue": gems.blue, "green": gems.green, "red": gems.red}

        logger.info(f"Game entry validation - Player: {player_id}, Game Type: {game_type}")
        logger.info(f"Entry cost: {entry_cost} tokens, Entry cost gems: {entry_cost_gems}")
        logger.info(f"Player balance: {token_balance} tokens, Player gems: {gems}")

        # Entry cost validation
        if game_type == "main":
            # Check if player has sufficient tokens
            if token_balance < entry_cost:
                logger.warning(f"Player {player_id} has insufficient tokens: {token_balance} < {entry_cost}")
                await sio.emit("error", {"message": f"Insufficient tokens. Required: {entry_cost}, Available: {token_balance}"}, to=sid)
                return
            
            # Check if player has sufficient gems for each color
            insufficient_gems = []
            for color in ["blue", "green", "red"]:
                required = entry_cost_gems.get(color, 0)
                available = gems.get(color, 0)
                if available < required:
                    insufficient_gems.append(f"{color}: {available}/{required}")
            
            if insufficient_gems:
                logger.warning(f"Player {player_id} has insufficient gems: {insufficient_gems}")
                await sio.emit("error", {"message": f"Insufficient gems: {', '.join(insufficient_gems)}"}, to=sid)
                return
                
        elif game_type == "quest":
            if token_balance < entry_cost:
                logger.warning(f"Player {player_id} has insufficient tokens for quest: {token_balance} < {entry_cost}")
                await sio.emit("error", {"message": f"Insufficient tokens for quest. Required: {entry_cost}, Available: {token_balance}"}, to=sid)
                return

        # Deduct entry cost
        update_fields = {"token_balance": token_balance - entry_cost}
        if game_type == "main":
            update_fields["gems"] = {
                color: gems.get(color, 0) - entry_cost_gems.get(color, 0)
                for color in ["blue", "green", "red"]
            }
        
        logger.info(f"Deducting from player {player_id}: {update_fields}")
        await db.players.update_one({"_id": ObjectId(player_id)}, {"$set": update_fields})

        # Create GameAttempt
        game_attempt = {
            "fk_player_id": ObjectId(player_id),
            "fk_game_configuration_id": game_level["fk_game_configuration_id"],
            "fk_game_level_id": game_level_id,
            "ip_address": ip_address,
            "device_fingerprint": device_fingerprint,
            "level_number": game_level["level_number"],
            "game_type": game_type,  # Add game_type field
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
            "updated_by": ObjectId(data.get("player_id")),
            "updated_at": datetime.utcnow(),
            "created_by": ObjectId(data.get("player_id")),
            "created_at": datetime.utcnow(),
        }
        result = await db.game_attempt.insert_one(game_attempt)
        game_attempt_id = result.inserted_id
        player_game_sessions[player_id] = game_attempt_id

        await sio.emit("game_joined", {
            "game_attempt_id": str(game_attempt_id),
            "message": "Game joined successfully"
        }, to=sid)

    except Exception as e:
        await sio.emit("error", {"message": f"Join game failed: {str(e)}"}, to=sid)

@sio.event
async def exit_game(sid, data):
    db = get_database()
    try:
        player_id = data.get("player_id")
        score = data.get("score")
        print("score",score)
        completion_percentage = data.get("completion_percentage")
        logger.info(f"Exit game request for player: {player_id}")
        
        game_attempt_id = player_game_sessions.pop(player_id, None)
        logger.info(f"Game attempt ID from sessions: {game_attempt_id}")

        if not game_attempt_id:
            await sio.emit("error", {"message": "No active game session to exit."}, to=sid)
            return

        end_time = datetime.utcnow()
        logger.info(f"End time: {end_time}")
        
        # game_attempt_id is already an ObjectId from player_game_sessions
        game_attempt = await db.game_attempt.find_one({"_id": game_attempt_id})
        game_level_configuration = await db.game_level_configuration.find_one({"_id": game_attempt.get("fk_game_level_id")})
        logger.info(f"Found game attempt: {game_attempt}")

        if not game_attempt:
            await sio.emit("error", {"message": "Game attempt not found."}, to=sid)
            return

        start_time = game_attempt.get("start_time", end_time)
        logger.info(f"Start time: {start_time}")
        
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Calculated duration: {duration} seconds")
        
        print("score",score)
        completion_percentage = game_attempt.get("completion_percentage", 0)
        entry_cost = game_attempt.get("entry_cost", 0)
        gems_spent = game_attempt.get("gems_spent", {"blue": 0, "green": 0, "red": 0})
        game_type = game_attempt.get("game_type", "main")
        Total_reward = entry_cost + game_level_configuration.get("reward_coins", 0)
        tokens_earned = round(Total_reward * (score / 100), 2)
        gems_earned = (
            {k: int(v * (score / 100)) for k, v in gems_spent.items()}
            if game_type == "main" else {"blue": 0, "green": 0, "red": 0}
        )

        logger.info(f"Updating game attempt with end_time: {end_time}, duration: {duration}")

        # Debug log before update
        print("Updating game_attempt", {
            "game_attempt_id": game_attempt_id,
            "end_time": end_time,
            "duration": duration,
            "tokens_earned": tokens_earned,
            "gems_earned": gems_earned
        })

        update_result = await db.game_attempt.update_one(
            {"_id": game_attempt_id},  # Already ObjectId, no need to wrap
            {
                "$set": {
                    "game_status": GameStatus.COMPLETED.value,
                    "end_time": end_time,
                    "duration": duration,
                    "tokens_earned": tokens_earned,
                    "gems_earned": gems_earned,
                    "score": score,
                    "completion_percentage": completion_percentage
                }
            }
        )
        
        logger.info(f"Update result: {update_result.modified_count} documents modified")

        # Create player transaction record
        try:
            # Get current player data for balance information
            player_doc = await db.players.find_one({"_id": ObjectId(player_id)})
            if player_doc:
                player_doc = decrypt_player_fields(player_doc)
                current_token_balance = player_doc.get("token_balance", 0)
                current_gems = player_doc.get("gems", {"blue": 0, "green": 0, "red": 0})
                if isinstance(current_gems, GemType):
                    current_gems = {"blue": current_gems.blue, "green": current_gems.green, "red": current_gems.red}
            else:
                current_token_balance = 0
                current_gems = {"blue": 0, "green": 0, "red": 0}

            # Determine transaction type based on tokens earned
            if tokens_earned > 0:
                transaction_type = PlayerTransactionType.REWARD
                description = f"Game reward earned: {tokens_earned} tokens"
                transaction_status = PlayerTransactionStatus.COMPLETED
            else:
                transaction_type = PlayerTransactionType.GAME_ENTRY
                description = f"Game entry cost: {entry_cost} tokens"
                transaction_status = PlayerTransactionStatus.COMPLETED

            # Create transaction record
            transaction_data = {
                "player_id": game_attempt.get("fk_player_id"),
                "transaction_type": transaction_type.value,
                "amount": tokens_earned,
                "fk_game_attempt_id": game_attempt_id,
                "fk_game_configuration_id": game_attempt.get("fk_game_configuration_id"),
                "current_total_amount": current_token_balance,
                "gems_earned": gems_earned,
                "gems_spent": gems_spent,
                "gems_balance": current_gems,
                "description": description,
                "transaction_status": transaction_status.value,
                "completed_at": datetime.utcnow()
            }

            # Insert transaction record
            transaction_result = await db.player_transaction.insert_one(transaction_data)
            logger.info(f"Player transaction created: {transaction_result.inserted_id} for player {player_id}")
            
        except Exception as e:
            logger.error(f"Error creating player transaction: {str(e)}")

        # Return rewards to player
        update = {"$inc": {"token_balance": tokens_earned}}
        if game_type == "main":
            update["$inc"].update({f"gems.{k}": gems_earned[k] for k in gems_earned})

        await db.players.update_one({"_id": ObjectId(player_id)}, update)

        await sio.emit("game_exited", {"message": "You have exited the game."}, to=sid)
        
    except Exception as e:
        logger.error(f"Error in exit_game: {str(e)}")
        await sio.emit("error", {"message": f"Exit game failed: {str(e)}"}, to=sid)

@sio.event
async def game_action(sid, data):
    db = get_database()
    try:
        player_id = data.get("player_id")
        action_type = data.get("action_type")  # MOVE, CLICK, DRAG, DROP, COMPLETE, FAIL
        action_data = data.get("action_data", {})
        session_id = data.get("session_id")
        
        game_attempt_id = player_game_sessions.get(player_id)
        if not game_attempt_id:
            await sio.emit("error", {"message": "No active game session"}, to=sid)
            return

        # Get the game attempt to extract required fields
        game_attempt = await db.game_attempt.find_one({"_id": game_attempt_id})
        if not game_attempt:
            await sio.emit("error", {"message": "Game attempt not found"}, to=sid)
            return

        # Validate action_type
        if action_type not in GameActionType.__members__:
            await sio.emit("error", {"message": f"Invalid action type. Must be one of: {list(GameActionType.__members__.keys())}"}, to=sid)
            return

        # Create game action entry
        game_action_entry = {
            "fk_game_attempt_id": game_attempt_id,
            "fk_game_configuration_id": game_attempt.get("fk_game_configuration_id"),
            "fk_player_id": game_attempt.get("fk_player_id"),
            "action_type": GameActionType[action_type].value,
            "action_data": action_data,
            "timestamp": datetime.utcnow(),
            "session_id": session_id
        }

        # Insert into game_action collection
        result = await db.game_action.insert_one(game_action_entry)
        logger.info(f"Game action logged: {action_type} for player {player_id}, action_id: {result.inserted_id}")

        # Update moves count in game_attempt
        await db.game_attempt.update_one(
            {"_id": game_attempt_id},
            {"$inc": {"moves_count": 1}}
        )

        await sio.emit("action_confirmed", {
            "game_attempt_id": str(game_attempt_id),
            "action_id": str(result.inserted_id),
            "action_type": action_type,
            "timestamp": data.get("timestamp")
        }, to=sid)

    except Exception as e:
        logger.error(f"Error in game_action: {str(e)}")
        await sio.emit("error", {"message": f"Game action failed: {str(e)}"}, to=sid)

@sio.event
async def game_state_update(sid, data):
    db = get_database()
    player_id = data.get("player_id")
    game_attempt_id = player_game_sessions.get(player_id)
    if not game_attempt_id:
        await sio.emit("error", {"message": "No active game session"}, to=sid)
        return

    await sio.emit("state_updated", {
        "game_attempt_id": str(game_attempt_id),
        "timestamp": data.get("timestamp")
    }, to=sid)

@sio.event
async def chat_message(sid, data):
    # Broadcast chat message to all clients
    await sio.emit("chat_message", {
        "player_id": data.get("player_id"),
        "username": data.get("username"),
        "message": data.get("message"),
        "timestamp": data.get("timestamp")
    })

@sio.event
async def ping(sid, data):
    await sio.emit("pong", {
        "timestamp": data.get("timestamp")
    }, to=sid)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=8000) 