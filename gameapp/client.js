const { io } = require("socket.io-client");
const readline = require('readline');

const playerId = "68832606c64d9f1408835893";

/*User-Agent: PostmanRuntime/7.44.1
Accept-Encoding: gzip, deflate, br
Accept: */


const socket = io("http://localhost:8000", {
  transports: ["websocket"],
  extraHeaders: {
    "x-device-fingerprint": "f333ac42a0a69d70cf11e9c43ab7adbb12ef8d68e45c6a3132901fba16392640",
    "x-client-ip": "127.0.0.1",
    "user_agent" : "PostmanRuntime/7.44.1", 
    "accept_language": "",
    "accept_encoding": "gzip, deflate, br",
    "cookie": "access_token=gAAAAABoi2BT5XO2_AhOWiQKv5JrShm7fY9phwo5-Zob5WvRt1mubOCmS6_LbJKAihq-3uQMld-CWbzYcwaBBTCf20k0MUjBTKpDLipCIuywowpcJvr-aCF5bOjKCtaD4WQT-GiVT9nhq1Wnd4qngpXWlwm0MEuEm_RbamT3eDa4otC9zyXUf3qwy-DSLoDa6yzro8lgTL5iDgKXXkY1djlo0pB5dzNB_U4v3Q3k0cQrJtja_ZZXyz2nz7sdl3ckJO5bjX0b-fS2GFro38PnyPGcT-mjZkqFfqyccWprz0w1GA7idP7mlE3cMtbfuDC6D71AbeP5RY0csKJNHmmQGPTkDrjEjpN3q0rVH2pon-7KUgfeRQjqqwR_3MdCoWsyBczFfO43XG0XL-Y9u_nhmNjbYNKi5e4tmmhqDbrGoTnVH53u_MSh1lMMgrnZ62awva3bKdEpnsJ91YEIPJ6dCkUGpKyIXdBGDi--uPmIFprYlF2LGY45y_1HQAw1hI2eTOnoJRW9_INZE1wu7axkSbzZQ-kYotvjD41Kxgyl_GfrRd11o4GmgkMhr_MZ3kILQkdCNbcRdmyo5YhU5JvmoabjgKSRjuYYLO5_cFctzElrPmuOhaJ2wCWkENBUIvIoP2er-hiPOWVcisRvRULWp3LGHgLiuIf3sneidFr3OX9EznYBf6lGfMYkJXi09Nz3U24SFIQZJH4CYU--XTt3eiKVa4kVBa63E9T_1nEA3UdMPLs6HtKJzy6lG4kix5cMi5yZx2iumZfW8tmcyhB5mCbYVgmFW3nNNE3hKC3fq371jvusVUrmN4TTJFH2uOp9oJ_IKK8AyDRQS31bgPQcIw9WrnsftogHMCQa93yuozU4F-zPvT9jnU4NHs1EQXWfYD6br5Y1lI7z0cswy0E6VauXQXpIbtpCLoEpepne-iqWGzH-fXDZzEwnIf7ZTM0TtJ74c84b7gPtfunJ9RB318SShhDwVFW_Nr08Xo2NK99mfXmHYCUhui4="

  },
  forceNew: true
});

// Handle connection
socket.on("connect", () => {
  console.log("✅ Connected to game server:", socket.id);

  socket.emit("join_game", {
    player_id: playerId,
    game_level_id: "6889cceb80a4ca85fcc3e372",
    game_type: "color_match",
    level_type: 2
  });
});

socket.on("game_joined", (data) => {
  console.log("🎮 Game Joined:", data);
});

socket.on("error", (err) => {
  console.error("❌ Error:", err.message || err);
});

socket.on("chat_message", (msg) => {
  console.log("💬 Chat:", msg);
});

socket.on("game_exited", (data) => {
  console.log("🚪 Exited Game:", data);
});

socket.on("action_confirmed", (data) => {
  console.log("✅ Action Confirmed:", data);
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
    player_id: playerId,
    score: 75,
    completion_percentage: 75,
    replay_data: []
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

// CLI input handling
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

// Periodic ping
setInterval(() => {
  socket.emit("ping", { timestamp: new Date().toISOString() });
}, 10000);
