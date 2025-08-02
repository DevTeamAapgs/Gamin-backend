import socketio
from fastapi import FastAPI, Request
from app.db.mongo import get_database, connect_to_mongo
from app.auth.cookie_auth import cookie_auth
from app.utils.crypto_utils import decrypt_player_fields, encrypt_player_fields
from app.utils.crypto import AESCipher
from app.models.game import GemType, GameAttempt, GameAction
from app.models.player import PlayerTransaction
from app.core.enums import GameStatus,PlayerTransactionStatus,PlayerTransactionType,GameActionType,LevelType
from app.core.constants import GEM_COLORS, DEFAULT_GEMS
from bson import ObjectId
from datetime import datetime
import logging
from http.cookies import SimpleCookie
import hashlib
from app.utils.request_utils import get_client_ip, generate_device_fingerprint
from app.services.game_engine import GameEngine
from app.schemas.game import JoinGameRequest, ExitGameRequest, GameActionRequest, GameStateUpdateRequest, ChatMessageRequest, PingRequest
from app.auth.cookie_auth import CookieAuth,get_current_user
logger = logging.getLogger(__name__)

# Store active player sessions
player_game_sessions = {}  # player_id: ObjectId of game_attempt

# Store socket headers for each connection
socket_headers = {}  # sid: {device_fingerprint, ip_address}

cookie_auth = CookieAuth()

def setup_socketio_routes(sio: socketio.AsyncServer, app: FastAPI):
    """
    Setup all Socket.IO event handlers and routes
    """
    
    # --- Connection Events ---

    @sio.event
    async def connect(sid, environ):
        db = get_database()

        # --- Extract headers ---
        headers = dict((k.decode(), v.decode()) for k, v in environ.get("headers", []))
        ip_address = headers.get("x-client-ip") or environ.get("HTTP_X_CLIENT_IP")

        # Create dummy request object for fingerprint generation
        class DummyRequest:
            def __init__(self, environ):
                # Extract headers from environ properly
                self.headers = {}
                for key, value in environ.items():
                    if key.startswith('HTTP_'):
                        # Convert HTTP_HEADER_NAME to header-name
                        header_name = key[5:].lower().replace('_', '-')
                        self.headers[header_name] = value
                self.client = type("Client", (), {"host": environ.get("REMOTE_ADDR", "unknown")})()
                
                # Add cookies attribute
                self.cookies = {}
                if 'HTTP_COOKIE' in environ:
                    cookie_header = environ['HTTP_COOKIE']
                    cookie_obj = SimpleCookie()
                    cookie_obj.load(cookie_header)
                    self.cookies = {key: morsel.value for key, morsel in cookie_obj.items()}

        request = DummyRequest(environ)
        player = await get_current_user(request)
        print("👤 Player:", player)
        # Example: Get a specific cookie (e.g., session or access token)
        access_token = cookie_auth.get_token_from_cookies(request)  # or your custom cookie name

        print("🍪 Cookies from client:", request.cookies)
        print("🔐 Access Token (if any):", access_token)
        
        # Always generate fingerprint using the same method as login
        fingerprint = generate_device_fingerprint(request)
        
        # If IP is missing, get it from the request
        if not ip_address:
            ip_address = get_client_ip(request)
        # Log extracted values
        print("🧩 Socket Connection Headers:")
        print("  ➤ IP Address:", ip_address)
        print("  ➤ Device Fingerprint:", fingerprint)
        print("  ➤ Raw headers:", headers)
        print("  ➤ Environ keys:", list(environ.keys()))

        # ✅ Validate session exists - try multiple approaches
        session_doc = None
        
        # First try: exact match with IP and fingerprint
        session_doc = await db.sessions.find_one({
            "ip_address": ip_address,
            "device_fingerprint": fingerprint,
            "status": 1,
            "dels": 1
        })
        print("session doc ",session_doc)
        

        if not session_doc:
            await sio.disconnect(sid)
            logger.warning(f"❌ Unauthorized connection. SID: {sid}, IP: {ip_address}, FP: {fingerprint}")
            return

        logger.info(f"✅ Connection authorized for player {session_doc['player_id']} with SID: {sid}")

        # Store headers for later use
        socket_headers[sid] = {
            "device_fingerprint": fingerprint,
            "ip_address": ip_address,
            "player_id": str(session_doc["player_id"]),
            "session_id": str(session_doc["_id"])
        }
        
    @sio.event
    async def disconnect(sid):
        logger.info(f"Client disconnected: {sid}")
        # Clean up stored headers
        if sid in socket_headers:
            del socket_headers[sid]
        # Optionally, clean up player_game_sessions here

    # --- Game Events ---

    @sio.event
    async def join_game(sid, data):
        db = get_database()
        try:
            try:
                data = JoinGameRequest(**data)
            except Exception as e:
                logger.error(f"Invalid join game data: {e}")
                await sio.emit("error", {"message": f"Invalid data format: {str(e)}"}, to=sid)
                return
            player_id = data.player_id
            game_level_id = ObjectId(data.game_level_id)
            game_type = data.game_type
            level_type = int(data.level_type)
            
            # Extract device fingerprint and IP from stored headers
            device_fingerprint = None
            ip_address = None
            
            # Get headers from stored socket headers
            print("🔍 Looking for headers for sid:", sid)
            print("📋 Available socket_headers keys:", list(socket_headers.keys()))
            if sid in socket_headers:
                stored_headers = socket_headers[sid]
                device_fingerprint = stored_headers.get("device_fingerprint")
                ip_address = stored_headers.get("ip_address")
                print("📍 Fingerprint from stored headers:", device_fingerprint)
                print("🌐 IP Address from stored headers:", ip_address)
            else:
                print("❌ No stored headers found for sid:", sid)
            
            # Fallback to data if not in stored headers
            if not device_fingerprint:
                device_fingerprint = data.device_fingerprint
            if not ip_address:
                ip_address = data.ip_address

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
            entry_cost_gems = game_level.get("entry_cost_gems", DEFAULT_GEMS)
            
            # Handle entry_cost_gems if it's a GemType object
            if isinstance(entry_cost_gems, GemType):
                entry_cost_gems = {"blue": entry_cost_gems.blue, "green": entry_cost_gems.green, "red": entry_cost_gems.red}
            
            token_balance = player_doc.get("token_balance", 0)
            gems = player_doc.get("gems", DEFAULT_GEMS)
            if isinstance(gems, GemType):
                gems = {"blue": gems.blue, "green": gems.green, "red": gems.red}

            logger.info(f"Game entry validation - Player: {player_id}, Game Type: {game_type}")
            logger.info(f"Entry cost: {entry_cost} tokens, Entry cost gems: {entry_cost_gems}")
            logger.info(f"Player balance: {token_balance} tokens, Player gems: {gems}")

            # Entry cost validation
            if entry_cost == 0 and all(entry_cost_gems.get(c, 0) == 0 for c in GEM_COLORS):
                logger.info(f"Player {player_id} joining free game.")
                game_attempt = {
                    "fk_player_id": ObjectId(player_id),
                    "fk_game_configuration_id": game_level["fk_game_configuration_id"],
                    "fk_game_level_id": game_level_id,
                    "ip_address": ip_address,
                    "device_fingerprint": device_fingerprint,
                    "level_number": game_level["level_number"],
                    "level_type": game_level["level_type"],
                    "game_status": GameStatus.ACTIVE.value,
                    "socket_id":sid,
                    "score": 0,
                    "tokens_earned": 0.0,
                    "gems_earned": DEFAULT_GEMS,
                    "entry_cost": 0,
                    "gems_spent": DEFAULT_GEMS,
                    "start_time": datetime.utcnow(),
                    "end_time": None,
                    "duration": None,
                    "moves_count": 0,
                    "max_moves": 100,
                    "game_data": {},  # or whatever initial state
                    "replay_data": [],
                    "completion_percentage": 0.0,
                    "updated_by": ObjectId(data.player_id),
                    "updated_at": datetime.utcnow(),
                    "created_by": ObjectId(data.player_id),
                    "created_at": datetime.utcnow(),
                }
                result = await db.game_attempt.insert_one(game_attempt)
                game_attempt_id = result.inserted_id
                player_game_sessions[player_id] = game_attempt_id

                await sio.emit("game_joined", {
                    "game_attempt_id": str(game_attempt_id),
                    "message": "Game joined successfully"
                }, to=sid)
                return
                
                # Skip validation for free games
            else:
                if token_balance < entry_cost:
                    logger.warning(f"Player {player_id} has insufficient tokens: {token_balance} < {entry_cost}")
                    await sio.emit("error", {"message": f"Insufficient tokens. Required: {entry_cost}, Available: {token_balance}"}, to=sid)
                    return
                
                insufficient_gems = []
                
                for color in GEM_COLORS:
                    required = entry_cost_gems.get(color, 0)
                    available = gems.get(color, 0)
                    if available < required:
                        insufficient_gems.append(f"{color}: {available}/{required}")
                    
                if insufficient_gems:
                    logger.warning(f"Player {player_id} has insufficient gems: {insufficient_gems}")
                    await sio.emit("error", {"message": f"Insufficient gems: {', '.join(insufficient_gems)}"}, to=sid)
                    return               
        

                # Calculate costs and rewards based on game_level_configuration
                entry_cost = game_level.get("entry_cost", 0)
                entry_cost_gems = game_level.get("entry_cost_gems", DEFAULT_GEMS)
                reward_coins = game_level.get("reward_coins", 0)
                reward_gems = game_level.get("reward_gems", DEFAULT_GEMS)
                
                # Handle gem objects if they're GemType instances
                if isinstance(entry_cost_gems, GemType):
                    entry_cost_gems = {"blue": entry_cost_gems.blue, "green": entry_cost_gems.green, "red": entry_cost_gems.red}
                if isinstance(reward_gems, GemType):
                    reward_gems = {"blue": reward_gems.blue, "green": reward_gems.green, "red": reward_gems.red}
                
                # Calculate what to deduct based on level_type
                tokens_to_deduct = entry_cost
                gems_to_deduct = entry_cost_gems
                
                # Deduct entry cost
                new_token_balance = token_balance - tokens_to_deduct
                new_gems = gems.copy()
                
                for color in GEM_COLORS:
                    new_gems[color] = gems.get(color, 0) - gems_to_deduct.get(color, 0)
                
                # Prepare update with new values
                update_fields = {"token_balance": new_token_balance, "gems": new_gems}
                
                # Encrypt the update fields before saving
                crypto = AESCipher()
                encrypted_update_fields = encrypt_player_fields(update_fields, crypto)
                
                logger.info(f"Deducting from player {player_id}: tokens={tokens_to_deduct}, gems={gems_to_deduct}")
                logger.info(f"New balance: tokens={new_token_balance}, gems={new_gems}")
                await db.players.update_one({"_id": ObjectId(player_id)}, {"$set": encrypted_update_fields})

                # Create player transaction record for entry cost
                try:
                    # Use the calculated values directly instead of reading from database
                    # This ensures we have the correct balance after deduction
                    current_token_balance = new_token_balance  # This is the balance after deduction
                    current_gems = new_gems  # This is the gems balance after deduction

                    # Create transaction record for game entry
                    transaction_data = {
                        "player_id": ObjectId(player_id),
                        "transaction_type": PlayerTransactionType.GAME_ENTRY.value,
                        "amount": -tokens_to_deduct,  # Negative amount since it's a deduction
                        "fk_game_attempt_id": None,  # Will be updated after game_attempt is created
                        "fk_game_configuration_id": game_level["fk_game_configuration_id"],
                        "current_total_amount": current_token_balance,  # Balance after entry cost deduction
                        "gems_earned": DEFAULT_GEMS,  # No gems earned on entry
                        "gems_spent": gems_to_deduct,  # Use the calculated gems_to_deduct
                        "gems_balance": current_gems,
                        "description": f"Game entry cost: {tokens_to_deduct} tokens",
                        "transaction_status": PlayerTransactionStatus.COMPLETED.value,
                        "completed_at": datetime.utcnow()
                    }

                    # Insert transaction record
                    transaction_result = await db.player_transaction.insert_one(transaction_data)
                    logger.info(f"Player transaction created for entry: {transaction_result.inserted_id} for player {player_id}")
                    logger.info(f"Entry transaction details - Amount: {transaction_data['amount']}, Current balance: {transaction_data['current_total_amount']}, Gems spent: {transaction_data['gems_spent']}")
                    
                except Exception as e:
                    logger.error(f"Error creating player transaction for entry: {str(e)}")

                # Calculate adaptive difficulty and generate game state
                print("player_id", player_id)
                print("game_level_id", game_level_id)
                print("game_type", game_type)
                print("level_type", level_type)
                print("game_level", game_level)
                game_engine = GameEngine()
                try:
                    difficulty = await game_engine.calculate_adaptive_difficulty(str(player_id), str(game_level_id))
                    print("difficulty", difficulty)
                except Exception as e:
                    print("Error in calculate_adaptive_difficulty:", e)
                    import traceback
                    print(traceback.format_exc())
                    raise

                try:
                    game_state = await game_engine.generate_game_state(game_type, game_level["level_number"], difficulty)
                    print("game_state", game_state)
                except Exception as e:
                    print("Error in generate_game_state:", e)
                    import traceback
                    print(traceback.format_exc())
                    raise

                # Create GameAttempt
                game_attempt = {
                    "fk_player_id": ObjectId(player_id),
                    "fk_game_configuration_id": game_level["fk_game_configuration_id"],
                    "fk_game_level_id": game_level_id,
                    "ip_address": ip_address,
                    "device_fingerprint": device_fingerprint,
                    "level_number": game_level["level_number"],
                    "level_type": game_level["level_type"],  # Add game_type field
                    "game_status": GameStatus.ACTIVE.value,
                    "score": 0,
                    "tokens_earned": 0.0,
                    "gems_earned": DEFAULT_GEMS,
                    "entry_cost": game_level["entry_cost"],
                    "gems_spent": entry_cost_gems,
                    "start_time": datetime.utcnow(),
                    "socket_id":sid,
                    "end_time": None,
                    "duration": None,
                    "moves_count": 0,
                    "max_moves": 100,
                    "game_data": game_state,
                    "replay_data": [],
                    "completion_percentage": 0.0,
                    "updated_by": ObjectId(data.player_id),
                    "updated_at": datetime.utcnow(),
                    "created_by": ObjectId(data.player_id),
                    "created_at": datetime.utcnow(),
                }
                result = await db.game_attempt.insert_one(game_attempt)
                game_attempt_id = result.inserted_id
                player_game_sessions[player_id] = game_attempt_id

                # Update the transaction record with the game_attempt_id
                try:
                    # Find the most recent transaction for this player and update it
                    # First find the transaction
                    recent_transaction = await db.player_transaction.find_one(
                        {
                            "player_id": ObjectId(player_id),
                            "transaction_type": PlayerTransactionType.GAME_ENTRY.value,
                            "fk_game_attempt_id": None
                        },
                        sort=[("completed_at", -1)]
                    )
                    
                    if recent_transaction:
                        # Update the found transaction
                        await db.player_transaction.update_one(
                            {"_id": recent_transaction["_id"]},
                            {
                                "$set": {
                                    "fk_game_attempt_id": game_attempt_id
                                }
                            }
                        )
                        logger.info(f"Updated transaction {recent_transaction['_id']} with game_attempt_id: {game_attempt_id}")
                    else:
                        logger.warning(f"No recent transaction found to update with game_attempt_id: {game_attempt_id}")
                except Exception as e:
                    logger.error(f"Error updating transaction with game_attempt_id: {str(e)}")

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
            try:
                data = ExitGameRequest(**data)
            except Exception as e:
                logger.error(f"Invalid exit game data: {e}")
                await sio.emit("error", {"message": f"Invalid data format: {str(e)}"}, to=sid)
                return
            player_id = data.player_id
            score = data.score
            print("score",score)
            completion_percentage = data.completion_percentage
            replay_data = data.replay_data
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
            # Use completion_percentage from request data, not from game_attempt
            entry_cost = game_attempt.get("entry_cost", 0)
            gems_spent = game_attempt.get("gems_spent", DEFAULT_GEMS)
            level_type = game_attempt.get("level_type", "main")
            print("level_type",level_type)
            
            # Calculate rewards based on game_level_configuration
            reward_coins = game_level_configuration.get("reward_coins", 0)
            reward_gems = game_level_configuration.get("reward_gems", DEFAULT_GEMS)
            
            # Handle gem objects if they're GemType instances
            if isinstance(reward_gems, GemType):
                reward_gems = {"blue": reward_gems.blue, "green": reward_gems.green, "red": reward_gems.red}
            
            # Calculate total possible reward
            total_possible_reward = entry_cost + reward_coins
            tokens_earned = round(total_possible_reward * (score / 100), 2)
            
            # Calculate gems earned based on score percentage
            gems_earned = {k: round(v * (score / 100)) for k, v in reward_gems.items()}
            print("gems_earned",gems_earned)
            
            logger.info(f"Reward calculation - Score: {score}, Total_possible_reward: {total_possible_reward}, Tokens_earned: {tokens_earned}")
            logger.info(f"Reward gems from config: {reward_gems}, Gems earned: {gems_earned}")

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
                        "completion_percentage": completion_percentage,
                        "replay_data": replay_data
                    }
                }
            )
            
            logger.info(f"Update result: {update_result.modified_count} documents modified")

            # Return rewards to player - need to decrypt current values first
            player_doc = await db.players.find_one({"_id": ObjectId(player_id)})
            if player_doc:
                player_doc = decrypt_player_fields(player_doc)
                current_token_balance = player_doc.get("token_balance", 0)
                current_gems = player_doc.get("gems", DEFAULT_GEMS)
                if isinstance(current_gems, GemType):
                    current_gems = {"blue": current_gems.blue, "green": current_gems.green, "red": current_gems.red}
                
                # Calculate new values
                new_token_balance = current_token_balance + tokens_earned
                new_gems = {}
                for color in GEM_COLORS:
                    new_gems[color] = current_gems.get(color, 0) + gems_earned.get(color, 0)
                
                # Prepare update with new values
                update_fields = {"token_balance": new_token_balance, "gems": new_gems}
                
                # Encrypt the update fields before saving
                crypto = AESCipher()
                encrypted_update = encrypt_player_fields(update_fields, crypto)
                
                await db.players.update_one({"_id": ObjectId(player_id)}, {"$set": encrypted_update})
                logger.info(f"Player balance updated - tokens_earned: {tokens_earned}, gems_earned: {gems_earned}")
            else:
                logger.error(f"Player not found: {player_id}")

            # Create player transaction record AFTER updating player balance
            try:
                # Get current player data for balance information AFTER adding rewards
                player_doc = await db.players.find_one({"_id": ObjectId(player_id)})
                if player_doc:
                    print("Raw player_doc gems after update:", player_doc.get("gems"))
                    player_doc = decrypt_player_fields(player_doc)
                    final_balance = player_doc.get("token_balance", 0)
                    final_gems = player_doc.get("gems", DEFAULT_GEMS)
                    if isinstance(final_gems, GemType):
                        final_gems = {"blue": final_gems.blue, "green": final_gems.green, "red": final_gems.red}
                    print("Final decrypted gems",final_gems)
                else:
                    final_balance = 0
                    final_gems = DEFAULT_GEMS

                # Determine transaction type based on tokens earned
                if tokens_earned > 0:
                    transaction_type = PlayerTransactionType.REWARD
                    description = f"Game reward earned: {tokens_earned} tokens"
                    transaction_status = PlayerTransactionStatus.COMPLETED

                # Create transaction record
                transaction_data = {
                    "player_id": game_attempt.get("fk_player_id"),
                    "transaction_type": transaction_type.value,
                    "amount": tokens_earned,
                    "fk_game_attempt_id": game_attempt_id,
                    "fk_game_configuration_id": game_attempt.get("fk_game_configuration_id"),
                    "current_total_amount": final_balance,  # Final balance after adding rewards
                    "gems_earned": gems_earned,
                    "gems_spent": DEFAULT_GEMS if transaction_type == PlayerTransactionType.REWARD else game_attempt.get("gems_spent", DEFAULT_GEMS),  # No gems spent for rewards, use from game_attempt for entry
                    "gems_balance": final_gems,  # Use final gems balance after update
                    "description": description,
                    "transaction_status": transaction_status.value,
                    "completed_at": datetime.utcnow()
                }

                # Insert transaction record
                transaction_result = await db.player_transaction.insert_one(transaction_data)
                logger.info(f"Player transaction created: {transaction_result.inserted_id} for player {player_id}")
                
            except Exception as e:
                logger.error(f"Error creating player transaction: {str(e)}")

            await sio.emit("game_exited", {"message": "You have exited the game."}, to=sid)
            
        except Exception as e:
            logger.error(f"Error in exit_game: {str(e)}")
            await sio.emit("error", {"message": f"Exit game failed: {str(e)}"}, to=sid)

    @sio.event
    async def game_action(sid, data):
        db = get_database()
        try:
            try:
                data = GameActionRequest(**data)
            except Exception as e:
                logger.error(f"Invalid game action data: {e}")
                await sio.emit("error", {"message": f"Invalid data format: {str(e)}"}, to=sid)
                return
                
            player_id = data.player_id
            action_type = data.action_type  # MOVE, CLICK, DRAG, DROP, COMPLETE, FAIL
            action_data = data.action_data
            session_id = data.session_id
            
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
                "action_data": action_data or {},
                "timestamp": datetime.utcnow(),
                "session_id": session_id or sid
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
                "timestamp": data.timestamp or datetime.utcnow().isoformat()
            }, to=sid)

        except Exception as e:
            logger.error(f"Error in game_action: {str(e)}")
            await sio.emit("error", {"message": f"Game action failed: {str(e)}"}, to=sid)

    @sio.event
    async def game_state_update(sid, data):
        db = get_database()
        data = GameStateUpdateRequest(**data)
        player_id = data.player_id
        game_attempt_id = player_game_sessions.get(player_id)
        if not game_attempt_id:
            await sio.emit("error", {"message": "No active game session"}, to=sid)
            return

        await sio.emit("state_updated", {
            "game_attempt_id": str(game_attempt_id),
            "timestamp": data.timestamp or datetime.utcnow().isoformat()
        }, to=sid)

    @sio.event
    async def chat_message(sid, data):
        # Broadcast chat message to all clients
        data = ChatMessageRequest(**data)
        await sio.emit("chat_message", {
            "player_id": data.player_id,
            "username": data.username,
            "message": data.message,
            "timestamp": data.timestamp or datetime.utcnow().isoformat()
        })

    @sio.event
    async def ping(sid, data):
        data = PingRequest(**data)
        await sio.emit("pong", {
            "timestamp": data.timestamp or datetime.utcnow().isoformat()
        }, to=sid)

    return sio
