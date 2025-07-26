from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from bson import ObjectId
import logging
import random
import math
from app.models.player import Player
from app.db.mongo import get_database
from app.core.config import settings

DIFFICULTY_CONFIG = {
    "alpha": 0.5,
    "decay_rate": 0.98,
    "metric_weights": {
        "accuracy": 0.4,
        "speed": 0.3,
        "efficiency": 0.3
    },
    "max_time": 60.0,
    "min_difficulty": 1.0,
    "max_difficulty": 2.0,
    "lookback_days": 30,
    "decay_lambda": 0.1
}

logger = logging.getLogger(__name__)

class GameEngine:
    def __init__(self):
        self.db = get_database()

    async def calculate_adaptive_difficulty(
        self, player_id: str, fk_game_level_id: str  ) -> float:
        now = datetime.utcnow()
        config = DIFFICULTY_CONFIG
        previous_difficulty = 1.0

        recent_games = await self.db.game_attempt.find({
            "player_id": player_id,
            "fk_game_level_id": ObjectId(fk_game_level_id),
            "start_time": {"$gte": now - timedelta(days=config["lookback_days"])}
        }).to_list(length=None)

        if not recent_games:
            return config["min_difficulty"]

        acc_scores, speed_scores, eff_scores, weights = [], [], [], []

        for game in recent_games:
            comp = game.get("completion_percentage", 0)
            duration = game.get("duration", config["max_time"]) or config["max_time"]
            moves = game.get("moves_count", 1)
            start_time = game.get("start_time", now)
            days_ago = max((now - start_time).days, 0)
            weight = math.exp(-config["decay_lambda"] * days_ago)

            acc = comp / 100
            speed = max(0, 1 - duration / config["max_time"])
            eff = min(1.0, comp / moves)

            acc_scores.append(acc)
            speed_scores.append(speed)
            eff_scores.append(eff)
            weights.append(weight)

        def wavg(vals, wts):
            return sum(v * w for v, w in zip(vals, wts)) / sum(wts) if wts else 0

        acc_score = wavg(acc_scores, weights)
        speed_score = wavg(speed_scores, weights)
        eff_score = wavg(eff_scores, weights)

        raw_score = (
            config["metric_weights"]["accuracy"] * acc_score +
            config["metric_weights"]["speed"] * speed_score +
            config["metric_weights"]["efficiency"] * eff_score
        )

        raw_difficulty = 1.0 + raw_score
        ema_difficulty = config["alpha"] * raw_difficulty + (1 - config["alpha"]) * previous_difficulty

        last_played = max([g["start_time"] for g in recent_games])
        idle_days = max((now - last_played).days, 0)
        decay = config["decay_rate"] ** idle_days
        final = ema_difficulty * decay

        return round(min(max(final, config["min_difficulty"]), config["max_difficulty"]), 2)

    async def generate_game_state(self, game_type: str, level: int, difficulty: float) -> Dict[str, Any]:
        if game_type == "color_match":
            return await self._generate_color_match_state(level, difficulty)
        elif game_type == "tube_filling":
            return await self._generate_tube_filling_state(level, difficulty)
        else:
            raise ValueError(f"Unknown game type: {game_type}")

    def calculate_capacity(self, level: int, difficulty: float, base_capacity: int = 4, max_capacity: int = 8, difficulty_multiplier: float = 0.5) -> int:
        """Calculate adaptive tube capacity based on level and difficulty."""
        raw_capacity = base_capacity + level * difficulty * difficulty_multiplier
        return min(int(round(raw_capacity)), max_capacity)
    
    def generate_flutter_hex_colors(self, n: int) -> List[str]:
        """Generate n distinct Flutter-compatible hex colors in 0xFFRRGGBB format."""
        colors = []
        for _ in range(n):
            rgb = random.randint(0x222222, 0xEEEEEE)
            hex_color = f"0xFF{rgb:06X}"  # Flutter format: ARGB
            while hex_color in colors:
                rgb = random.randint(0x222222, 0xEEEEEE)
                hex_color = f"0xFF{rgb:06X}"
            colors.append(hex_color)
        return colors


    async def _generate_color_match_state(self, level: int, difficulty: float) -> Dict[str, Any]:
        """Generate color match game state with hex colors."""
        base_colors = 3
        max_colors = 8

        colors_count = min(int(round(base_colors + level * difficulty)), max_colors)
        capacity = self.calculate_capacity(level, difficulty)

        max_empty_tubes = 2
        min_empty_tubes = 1
        empty_tube_buffer = max(min_empty_tubes, max_empty_tubes - int((difficulty - 1.0) * 2))
        total_tubes = colors_count + empty_tube_buffer

        # Generate unique hex colors
        hex_colors = self.generate_flutter_hex_colors(colors_count)

        color_distribution = []
        for color in hex_colors:
            color_distribution.extend([color] * capacity)

        random.shuffle(color_distribution)

        tubes_state = []
        for i in range(total_tubes):
            start = i * capacity
            end = start + capacity
            tube = color_distribution[start:end] if start < len(color_distribution) else []
            tubes_state.append(tube)

        return {
            "game_type": "color_match",
            "level": level,
            "difficulty": difficulty,
            "colors": colors_count,
            "hex_color_map": hex_colors,
            "tubes": total_tubes,
            "capacity": capacity,
            "tubes_state": tubes_state,
            "target_state": self._solve_color_match(tubes_state, capacity)
        }
    def _solve_color_match(self, tubes_state: List[List[int]], capacity: int = 4) -> List[List[int]]:
        color_buckets = {}
        for tube in tubes_state:
            for color in tube:
                color_buckets.setdefault(color, []).append(color)

        solution = []
        for color, items in sorted(color_buckets.items()):
            for i in range(0, len(items), capacity):
                solution.append(items[i:i + capacity])

        while len(solution) < len(tubes_state):
            solution.append([])

        return solution

    async def _generate_tube_filling_state(self, level: int, difficulty: float) -> Dict[str, Any]:
        return {}

    async def validate_game_completion(self, game_id: str, submitted_state: Dict[str, Any]) -> Dict[str, Any]:
        game = await self.db.games.find_one({"_id": game_id})
        if not game:
            raise ValueError("Game not found")

        game_state = game.get("game_state", {})
        target_state = game_state.get("target_state", [])

        completion_percentage = self._calculate_completion_percentage(submitted_state, target_state)
        cheat_detection = await self._detect_cheating(game_id, submitted_state)

        return {
            "completion_percentage": completion_percentage,
            "is_valid": completion_percentage >= 0,
            "cheat_detected": cheat_detection["detected"],
            "cheat_reason": cheat_detection["reason"]
        }

    def _calculate_completion_percentage(self, submitted_state: Dict[str, Any], target_state: List[List[int]]) -> float:
        if not submitted_state or not target_state:
            return 0.0

        submitted_tubes = submitted_state.get("tubes_state", [])
        if len(submitted_tubes) != len(target_state):
            return 0.0

        submitted_flat = [color for tube in submitted_tubes for color in tube]
        target_flat = [color for tube in target_state for color in tube]

        match_count = 0
        used_indices = set()

        for color in submitted_flat:
            for i, t_color in enumerate(target_flat):
                if i not in used_indices and color == t_color:
                    match_count += 1
                    used_indices.add(i)
                    break

        return (match_count / len(target_flat)) * 100 if target_flat else 0.0

    async def _detect_cheating(self, game_id: str, submitted_state: Dict[str, Any]) -> Dict[str, Any]:
        replay = await self.db.replays.find_one({"game_id": game_id})
        if not replay:
            return {"detected": False, "reason": None}

        actions = replay.get("action_sequence", [])
        timing_data = replay.get("timing_data", {})

        if self._detect_speed_hack(timing_data):
            return {"detected": True, "reason": "Speed hack detected"}

        if self._detect_repetitive_patterns(actions):
            return {"detected": True, "reason": "Repetitive pattern detected"}

        if self._detect_unnatural_movements(replay.get("mouse_movements", [])):
            return {"detected": True, "reason": "Unnatural movements detected"}

        return {"detected": False, "reason": None}

    def _detect_speed_hack(self, timing_data: Dict[str, Any]) -> bool:
        return False

    def _detect_repetitive_patterns(self, actions: List[Dict[str, Any]]) -> bool:
        return False

    def _detect_unnatural_movements(self, mouse_movements: List[Dict[str, Any]]) -> bool:
        return False

game_engine = GameEngine()
