const { io } = require("socket.io-client");
const readline = require('readline');
const fs = require('fs');

// Configuration
const CONFIG = {
  serverUrl: "http://localhost:8000",
  playerId: "685f794d79d0e77a1e25d5a2",
  gameLevelId: "687f17fb4f002aa7e81e10e4",
  gameType: "color_match",
  levelType: 2,
  reconnectAttempts: 5,
  reconnectDelay: 2000,
  pingInterval: 10000,
  logToFile: true,
  logFile: "client_log.json"
};

// Logging utility
class Logger {
  constructor() {
    this.logs = [];
    this.startTime = new Date();
  }

  log(message, type = 'info', data = null) {
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      type,
      message,
      data,
      sessionId: this.sessionId || 'unknown'
    };

    this.logs.push(logEntry);

    const prefix = {
      'info': 'ℹ️',
      'success': '✅',
      'error': '❌',
      'warning': '⚠️',
      'game': '🎮',
      'chat': '💬',
      'action': '⚡'
    }[type] || 'ℹ️';

    console.log(`${prefix} [${timestamp}] ${message}`);
    
    if (data) {
      console.log(`   📊 Data: ${JSON.stringify(data, null, 2)}`);
    }
  }

  saveLogs() {
    if (CONFIG.logToFile) {
      try {
        const logData = {
          sessionStart: this.startTime.toISOString(),
          sessionEnd: new Date().toISOString(),
          totalLogs: this.logs.length,
          logs: this.logs
        };
        
        fs.writeFileSync(CONFIG.logFile, JSON.stringify(logData, null, 2));
        console.log(`📝 Logs saved to ${CONFIG.logFile}`);
      } catch (error) {
        console.error(`❌ Failed to save logs: ${error.message}`);
      }
    }
  }

  setSessionId(sessionId) {
    this.sessionId = sessionId;
  }
}

// Enhanced Socket Client
class GameClient {
  constructor() {
    this.socket = null;
    this.logger = new Logger();
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.gameState = {
      joined: false,
      currentLevel: null,
      score: 0,
      actions: []
    };
    this.rl = null;
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.logger.log("Connecting to game server...", 'info');

      this.socket = io('http://127.0.0.1:8000', {
        transports: ["websocket"],
        extraHeaders: {
          "x-device-fingerprint": "f333ac42a0a69d70cf11e9c43ab7adbb12ef8d68e45c6a3132901fba16392640",
          "x-client-ip": "127.0.0.1",
          "user_agent": "EnhancedGameClient/2.0.0",
          "accept_language": "en-US,en;q=0.9",
          "accept_encoding": "gzip, deflate, br",
          "cookie": "access_token=gAAAAABokyvDQlakReooXszoFA-A8VVo2GRb_kYNtDCiWxAA8JODrbPrSQZ1_SbBzBjxXXj1T70k0dXMwVKilrxjxGg0-U0DsID0abTFRpoDib04gsO2A3xLe3Bc5PDoRMiEa9k6vjj8G_NV-PGn54uIAGe43JFD24vN0bLBNzuQP8uBQM6LPxmB-6WmdEBqeFbPnlDFmiEnni2oZ8SqB-nex04Qww7jqIIahwHbM-dFbAVanfaUmo9AtxZnOgpEnoVGBtMAc_TqwXwUslJAiCrGp3kHwT8LrkhVm_QZ8fjnLANQBjh_HR7rhFBKIoqugnMgQ7Gqz9ckKugu_YOTiS_gWvG-W38YgfgpYrW5g5WKNzg8FRKcPa3joidVWMgaJ5l4sQU1Z9fkNLUFRDq7Nq1E8SVfKSl2HMBzOFFCD9iyLd8sD1Y5moxjBQAgVeZI__wTNWRtclJe0pv5zpoWHDUtBxTB0W66PdsR9Pd7I2pUDx8a4S1fJFz9q4Q2w_BXWEgIbkn3f_EHggT4m9gwESiTONFJJl0RFlMc1ZduIbh5yjxxpAnFCLos8R3GZiROLQcVzDtUV4ymSTybrE_-pVP43tSzqV7aMXx0RDbXI0SshlJXtN_sJAAu913GqzLeTCVYItAItZijGPETwmxj-BshMQyn16UJ1EQYSzaqhkAIBXUTuETvHJitXkQhXrqlQ2htHXPqH7JhyvTEbRksR8a8AJzBw0FDquFKzJWeReC3O5WKVk0O6pivdQqLBvudxaeF3tXmfrqyaSnxXZwPmn2z_Wx3C-FC2Zymv-MEZRBvp5GMHJyDKuzB8fInC2w7Aa4EmzxvOI5dLwNGuR1CAdu77v4egeJrZ8zE3Mh0uSA9uzs4yTK6pXkzzZ-eGg7_8WNHxin2IcpOr_bnj6Zj4EKMHC1W7xnA0SzeNOuQFDoBuMpR0DX2eRhBWARO9EaS_p5OTvV23dkxfz2DE_rv50iCJcA8XcRrqszpa6HkxQZivGWGGNH81lU=, refresh_token=gAAAAABokyvDP6LKpW7uaculFgvJiTJ8DUHr38vhWJ-bD9pI1_xFHpNw47-O-aX9fYnFMJOOvlzgFVK8imo_qLs6TOJlOSdzsOS-Kr0J3U7vlVjVJoXtDuwUgrK0r35zdtF1cu21yVAzROZ_dRajdV4JTCUSufR1zoF7eVMZNWFWYwPxwrPii-bKxjK3rMzk6tOWbcJcnI4FOeCeCwP_RnWb9tw1GYxsJ_ySgc89n6HVsthV4o8z2C31as_LwL-pz-e7JRlEZGi8yF0ZPpo1Azi5iohk3LF_nXq9bCkY-S8gZyGOoeEa0bIq3YHQYhb0Lnwmj2a0GnsAgVxIwnhT_tnwkRToQiSmrwFBvlJS9ptAEshyAIPCo9PyBUTHJ4vA_aFIhU9Kvbl-bqsanJDpoC0J2_IHLTBdQUuWe0R3eeRMRYWb-iAG_MQJz4ozdVD9zHEQ0YsXGAQtyPO1Fn0QppMVRDkI70M7N29QMb8IMtsBNWQyisL1SGFJNQd4YdU9tlUWXsTiGvyzSPVEj22i5k3-RxGLVc_VguWZHSCKKfTto8maq_RV3a2qlAh9iCO9927ld2dvv-BXfI7sV104f6jrU7tPeLigtzDbn8sYNZmxe4I5BTw81q-GGt_ZiZRgj_C-G4K92Q9bXIs5FIHQsIXMZy1Qc3ydXygAiA9PXP3pda__hzT4kqdz9qWw2WSCGJ8b7CZJpvKt52qewZ4E_r88beWQ0unYfAi_uiYPmcjfvEjgn8zxe_6PaaLuvzfoLuO4-zZF0qHOQkzhw-2BMf2n2x98dZZYJwYW4HVJAMF_KIM0vPX2kTMUonl_Ahw5FxcJa0fRm1LWeTmAZvJATPxF2cXihRpv4sl0-t9qIyMPso_WYGB1_g-dYy-16SRC5oXH3TP5XFNP1JYPOMOXDX_eBbVZel_hDfg9tdc89tCsiMYgUaNULgzduOxSxFkY-1_aMHoNdpglq8rjD2y3auVIADyjUrOScR7Qw4ccfhA4-nLfoqsbB6c="
        },
        forceNew: true,
        reconnection: true,
        reconnectionAttempts: CONFIG.reconnectAttempts,
        reconnectionDelay: CONFIG.reconnectDelay
      });

      this.setupEventListeners();

      this.socket.on("connect", () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.logger.setSessionId(this.socket.id);
        this.logger.log(`Connected to game server with session ID: ${this.socket.id}`, 'success');
        
        // Auto-join game after connection
        this.joinGame();
        resolve(this.socket);
      });

      this.socket.on("connect_error", (error) => {
        this.logger.log(`${error}`);
        this.logger.log(`Connection failed: ${error.message}`, 'error');
        reject(error);
      });

      // Connection timeout
      setTimeout(() => {
        if (!this.isConnected) {
          reject(new Error("Connection timeout"));
        }
      }, 10000);
    });
  }

  setupEventListeners() {
    // Connection events
    this.socket.on("disconnect", (reason) => {
      this.isConnected = false;
      this.logger.log(`Disconnected: ${reason}`, 'warning');
      
      if (reason === 'io server disconnect') {
        // Server disconnected us, try to reconnect
        this.socket.connect();
      }
    });

    this.socket.on("reconnect", (attemptNumber) => {
      this.logger.log(`Reconnected after ${attemptNumber} attempts`, 'success');
      this.isConnected = true;
      this.joinGame(); // Re-join game after reconnection
    });

    this.socket.on("reconnect_error", (error) => {
      this.logger.log(`Reconnection failed: ${error.message}`, 'error');
    });

    // Game events
    this.socket.on("game_joined", (data) => {
      this.gameState.joined = true;
      this.gameState.currentLevel = data;
      this.logger.log("Successfully joined game", 'game', data);
    });

    this.socket.on("error", (err) => {
      this.logger.log(`Game error: ${err.message || err}`, 'error');
    });

    this.socket.on("chat_message", (msg) => {
      this.logger.log(`Chat message: ${msg.message}`, 'chat', msg);
    });

    this.socket.on("game_exited", (data) => {
      this.gameState.joined = false;
      this.logger.log("Game exited", 'game', data);
    });

    this.socket.on("action_confirmed", (data) => {
      this.logger.log("Action confirmed by server", 'action', data);
    });

    this.socket.on("game_state_update", (data) => {
      this.logger.log("Game state updated", 'game', data);
    });
  }

  joinGame() {
    if (!this.isConnected) {
      this.logger.log("Cannot join game: not connected", 'error');
      return;
    }

    const joinData = {
      player_id: CONFIG.playerId,
      game_level_id: CONFIG.gameLevelId,
      game_type: CONFIG.gameType,
      level_type: CONFIG.levelType
    };

    this.logger.log("Joining game...", 'game', joinData);
    this.socket.emit("join_game", joinData);
  }

  sendChat(message, username = "tester") {
    if (!this.isConnected) {
      this.logger.log("Cannot send chat: not connected", 'error');
      return;
    }

    const chatData = {
      player_id: CONFIG.playerId,
      username: username,
      message: message,
      timestamp: new Date().toISOString()
    };

    this.logger.log(`Sending chat: ${message}`, 'chat');
    this.socket.emit("chat_message", chatData);
  }

  sendGameAction(actionType, actionData = {}) {
    if (!this.isConnected) {
      this.logger.log("Cannot send action: not connected", 'error');
      return;
    }

    const action = {
      player_id: CONFIG.playerId,
      action_type: actionType,
      action_data: actionData,
      session_id: this.socket.id,
      timestamp: new Date().toISOString()
    };

    this.gameState.actions.push(action);
    this.logger.log(`Sending game action: ${actionType}`, 'action', action);
    this.socket.emit("game_action", action);
  }

  async exitGame(score = 75, completionPercentage = 75) {
    if (!this.isConnected) {
      this.logger.log("Cannot exit game: not connected", 'error');
      return;
    }

    return new Promise((resolve, reject) => {
      const exitData = {
        player_id: CONFIG.playerId,
        score: score,
        completion_percentage: completionPercentage,
        replay_data: this.gameState.actions
      };

      this.logger.log("Exiting game...", 'game', exitData);
      
      this.socket.emit("exit_game", exitData, (response) => {
        if (response && response.success) {
          this.logger.log("Game exited successfully", 'success', response);
          resolve(response);
        } else {
          this.logger.log("Failed to exit game", 'error', response);
          reject(new Error("Exit game failed"));
        }
      });
    });
  }

  startPingInterval() {
    setInterval(() => {
      if (this.isConnected) {
        this.socket.emit("ping", { 
          timestamp: new Date().toISOString(),
          session_id: this.socket.id
        });
      }
    }, CONFIG.pingInterval);
  }

  setupCLI() {
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });

    console.log("\n🎮 Enhanced Game Client Commands:");
    console.log("  chat <message>     - Send chat message");
    console.log("  move               - Send move action");
    console.log("  click              - Send click action");
    console.log("  drag               - Send drag action");
    console.log("  drop               - Send drop action");
    console.log("  complete           - Send level complete action");
    console.log("  fail               - Send level fail action");
    console.log("  status             - Show current game status");
    console.log("  exit               - Exit game and disconnect");
    console.log("  help               - Show this help message");
    console.log("=".repeat(50));

    this.rl.on("line", (input) => {
      this.handleCommand(input.trim());
    });
  }

  handleCommand(input) {
    const parts = input.split(' ');
    const cmd = parts[0].toLowerCase();
    const args = parts.slice(1);

    switch (cmd) {
      case 'chat':
        if (args.length > 0) {
          this.sendChat(args.join(' '));
        } else {
          console.log("❌ Usage: chat <message>");
        }
        break;

      case 'move':
        this.sendGameAction("MOVE", {
          direction: "up",
          position: { x: 10, y: 20 },
          tile_from: { row: 1, col: 2 },
          tile_to: { row: 1, col: 3 },
          move_number: 1
        });
        break;

      case 'click':
        this.sendGameAction("CLICK", {
          position: { x: 100, y: 150 },
          target: "button",
          element_id: "btn_play",
          click_type: "left_click",
          click_number: 1
        });
        break;

      case 'drag':
        this.sendGameAction("DRAG", {
          start: { x: 50, y: 50 },
          end: { x: 100, y: 100 },
          dragged_item: "gem_blue",
          drag_duration: 2.5,
          drag_distance: 70.7
        });
        break;

      case 'drop':
        this.sendGameAction("DROP", {
          position: { x: 100, y: 100 },
          item: "gem_blue",
          drop_target: "slot_1",
          drop_success: true,
          combo_created: false
        });
        break;

      case 'complete':
        this.sendGameAction("COMPLETE", {
          level: 1,
          score: 100,
          completion_time: 120.5,
          stars_earned: 3,
          bonus_points: 50
        });
        break;

      case 'fail':
        this.sendGameAction("FAIL", {
          reason: "timeout",
          attempts: 3,
          time_remaining: 0,
          failed_at_position: { x: 150, y: 200 }
        });
        break;

      case 'status':
        console.log("\n📊 Current Game Status:");
        console.log(`  Connected: ${this.isConnected ? '✅' : '❌'}`);
        console.log(`  Session ID: ${this.socket?.id || 'N/A'}`);
        console.log(`  Game Joined: ${this.gameState.joined ? '✅' : '❌'}`);
        console.log(`  Current Level: ${JSON.stringify(this.gameState.currentLevel)}`);
        console.log(`  Actions Sent: ${this.gameState.actions.length}`);
        console.log(`  Score: ${this.gameState.score}`);
        break;

      case 'exit':
        this.cleanup();
        break;

      case 'help':
        console.log("\n🎮 Available Commands:");
        console.log("  chat <message>     - Send chat message");
        console.log("  move               - Send move action");
        console.log("  click              - Send click action");
        console.log("  drag               - Send drag action");
        console.log("  drop               - Send drop action");
        console.log("  complete           - Send level complete action");
        console.log("  fail               - Send level fail action");
        console.log("  status             - Show current game status");
        console.log("  exit               - Exit game and disconnect");
        console.log("  help               - Show this help message");
        break;

      default:
        console.log("❓ Unknown command. Type 'help' for available commands.");
        break;
    }
  }

  async cleanup() {
    this.logger.log("Cleaning up and exiting...", 'info');
    
    try {
      if (this.gameState.joined) {
        await this.exitGame();
      }
    } catch (error) {
      this.logger.log(`Error during exit: ${error.message}`, 'error');
    }

    if (this.rl) {
      this.rl.close();
    }

    if (this.socket) {
      this.socket.disconnect();
    }

    this.logger.saveLogs();
    process.exit(0);
  }
}

// Main execution
async function main() {
  const client = new GameClient();

  // Handle Ctrl+C gracefully
  process.on("SIGINT", () => {
    console.log("\n🛑 Ctrl+C detected. Cleaning up...");
    client.cleanup();
  });

  try {
    console.log("🚀 Starting Enhanced Game Client...");
    console.log(`📡 Server: ${CONFIG.serverUrl}`);
    console.log(`👤 Player ID: ${CONFIG.playerId}`);
    console.log(`🎮 Game Level: ${CONFIG.gameLevelId}`);
    console.log("=".repeat(50));

    await client.connect();
    client.startPingInterval();
    client.setupCLI();

  } catch (error) {
    console.error(`❌ Failed to start client: ${error.message}`);
    process.exit(1);
  }
}

// Run if this file is executed directly
if (require.main === module) {
  main();
}

module.exports = { GameClient, CONFIG };
