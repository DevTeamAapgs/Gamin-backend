const { io } = require("socket.io-client");
const readline = require('readline');

const playerId = "68832606c64d9f1408835893"; // Set this once to avoid duplication

const socket = io("http://localhost:8000", {
  transports: ["websocket"],
});

// Handle connection
socket.on("connect", () => {
  console.log("✅ Connected to game server:", socket.id);

  // Emit join_game event
  socket.emit("join_game", {
    player_id: playerId,
    game_level_id: "687f17fb4f002aa7e81e10e4",
    game_type: "main",
    device_fingerprint: "abcdef123457",
    ip_address: "192.168.1.5"
  });
});

// Listen for confirmation
socket.on("game_joined", (data) => {
  console.log("🎮 Game Joined:", data);
});

// Listen for errors
socket.on("error", (err) => {
  console.error("❌ Error:", err.message || err);
});

// Send chat message
function sendChat() {
  socket.emit("chat_message", {
    player_id: playerId,
    username: "tester",
    message: "Hello from client!",
    timestamp: new Date().toISOString()
  });
}

// Send game action
function sendGameAction(actionType, actionData = {}) {
  socket.emit("game_action", {
    player_id: playerId,
    action_type: actionType,
    action_data: actionData,
    session_id: socket.id,
    timestamp: new Date().toISOString()
  });
}

// Exit game gracefully
function exitGame() {
  console.log("👋 Exiting game...");
  socket.emit("exit_game", {
    player_id: playerId,score : 75, completion_percentage : 75
  }, (response) => {
    console.log("✅ Exit Response:", response);
    socket.disconnect();
    process.exit(0);
  });
}

// Ctrl+C handling
process.on("SIGINT", () => {
  console.log("🛑 Ctrl+C detected. Disconnecting...");
  exitGame();
});

// CLI interaction
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});


console.log("💡 Commands: 'chat', 'move', 'click', 'drag', 'drop', 'complete', 'fail', or 'exit'");
rl.on("line", (input) => {
  const cmd = input.trim().toLowerCase();
  if (cmd === "exit") {
    exitGame();
    rl.close();
  } else if (cmd === "chat") {
    sendChat();
  } else if (cmd === "move") {
    sendGameAction("MOVE", { 
      direction: "up", 
      position: { x: 10, y: 20 },
      tile_from: { row: 1, col: 2 },
      tile_to: { row: 1, col: 3 },
      move_number: 1
    });
  } else if (cmd === "click") {
    sendGameAction("CLICK", { 
      position: { x: 100, y: 150 }, 
      target: "button",
      element_id: "btn_play",
      click_type: "left_click",
      click_number: 1
    });
  } else if (cmd === "drag") {
    sendGameAction("DRAG", { 
      start: { x: 50, y: 50 }, 
      end: { x: 100, y: 100 },
      dragged_item: "gem_blue",
      drag_duration: 2.5,
      drag_distance: 70.7
    });
  } else if (cmd === "drop") {
    sendGameAction("DROP", { 
      position: { x: 100, y: 100 }, 
      item: "gem_blue",
      drop_target: "slot_1",
      drop_success: true,
      combo_created: false
    });
  } else if (cmd === "complete") {
    sendGameAction("COMPLETE", { 
      level: 1, 
      score: 100,
      completion_time: 120.5,
      stars_earned: 3,
      bonus_points: 50
    });
  } else if (cmd === "fail") {
    sendGameAction("FAIL", { 
      reason: "timeout", 
      attempts: 3,
      time_remaining: 0,
      failed_at_position: { x: 150, y: 200 }
    });
  } else {
    console.log("❓ Unknown command. Use: chat, move, click, drag, drop, complete, fail, or exit");
  }
});

// Other event listeners
socket.on("chat_message", (msg) => {
  console.log("💬 Chat:", msg);
});

socket.on("game_exited", (data) => {
  console.log("🚪 Exited Game:", data);
});

socket.on("action_confirmed", (data) => {
  console.log("✅ Action Confirmed:", data);
});

// Periodic ping to server
setInterval(() => {
  socket.emit("ping", { timestamp: new Date().toISOString() });
}, 10000);
