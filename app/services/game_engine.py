from datetime import datetime
from typing import Dict, Any, List, Optional
# from app.models.game import Game, GameAttempt, GameLevel
from app.models.player import Player
from app.db.mongo import get_database
from app.core.config import settings
import logging
import random

logger = logging.getLogger(__name__)

class GameEngine:
    def __init__(self):
        self.db = get_database()
    
    async def calculate_reward(self, completion_percentage: float, entry_cost: float, reward_multiplier: float) -> float:
        """Calculate reward based on completion percentage."""
        if completion_percentage >= 80:
            reward = entry_cost * reward_multiplier * 1.5
        elif completion_percentage >= 50:
            reward = entry_cost * reward_multiplier * 0.75
        else:
            reward = entry_cost * reward_multiplier * 0.3
        
        return round(reward, 2)
    
    async def calculate_adaptive_difficulty(self, player_id: str, game_type: str, level: int, attempt_number: int) -> float:
        """Calculate adaptive difficulty based on player performance."""
        # Get player's recent performance
        recent_games = await self.db.games.find({
            "player_id": player_id,
            "game_type": game_type,
            "level": level
        }).sort("created_at", -1).limit(5).to_list(length=5)
        
        if not recent_games:
            return 1.0  # Base difficulty
        
        # Calculate average completion percentage
        avg_completion = sum(game.get("completion_percentage", 0) for game in recent_games) / len(recent_games)
        
        # Adjust difficulty based on performance
        if avg_completion > 80:
            # Player is doing well, increase difficulty
            difficulty_multiplier = 1.0 + (attempt_number * 0.2)
        elif avg_completion > 50:
            # Player is doing okay, slight increase
            difficulty_multiplier = 1.0 + (attempt_number * 0.1)
        else:
            # Player is struggling, keep difficulty manageable
            difficulty_multiplier = 1.0 + (attempt_number * 0.05)
        
        return min(difficulty_multiplier, 2.0)  # Cap at 2x difficulty
    
    async def generate_game_state(self, game_type: str, level: int, difficulty: float) -> Dict[str, Any]:
        """Generate game state based on type, level, and difficulty."""
        if game_type == "color_match":
            return await self._generate_color_match_state(level, difficulty)
        elif game_type == "tube_filling":
            return await self._generate_tube_filling_state(level, difficulty)
        else:
            raise ValueError(f"Unknown game type: {game_type}")
    
    async def _generate_color_match_state(self, level: int, difficulty: float) -> Dict[str, Any]:
        """Generate color match game state."""
        # Base configuration
        base_colors = 3
        base_tubes = 4
        base_capacity = 4
        
        # Scale with level and difficulty
        colors = min(base_colors + level, 8)
        tubes = base_tubes + level
        capacity = base_capacity + int(level * 0.5)
        
        # Generate color distribution
        color_distribution = []
        for i in range(colors):
            color_count = capacity
            color_distribution.extend([i] * color_count)
        
        # Shuffle colors
        random.shuffle(color_distribution)
        
        # Distribute to tubes
        tubes_state = []
        for i in range(tubes):
            tube_colors = color_distribution[i * capacity:(i + 1) * capacity]
            tubes_state.append(tube_colors)
        
        return {
            "game_type": "color_match",
            "level": level,
            "difficulty": difficulty,
            "colors": colors,
            "tubes": tubes,
            "capacity": capacity,
            "tubes_state": tubes_state,
            "target_state": self._solve_color_match(tubes_state)
        }
    
    async def _generate_tube_filling_state(self, level: int, difficulty: float) -> Dict[str, Any]:
        """Generate tube filling game state."""
        # Base configuration
        base_tubes = 3
        base_liquids = 2
        
        # Scale with level and difficulty
        tubes = base_tubes + level
        liquids = base_liquids + int(level * 0.5)
        
        # Generate liquid distribution
        liquid_distribution = []
        for i in range(liquids):
            liquid_count = tubes
            liquid_distribution.extend([i] * liquid_count)
        
        # Shuffle liquids
        random.shuffle(liquid_distribution)
        
        # Distribute to tubes
        tubes_state = []
        for i in range(tubes):
            tube_liquids = liquid_distribution[i * tubes:(i + 1) * tubes]
            tubes_state.append(tube_liquids)
        
        return {
            "game_type": "tube_filling",
            "level": level,
            "difficulty": difficulty,
            "tubes": tubes,
            "liquids": liquids,
            "tubes_state": tubes_state,
            "target_state": self._solve_tube_filling(tubes_state)
        }
    
    def _solve_color_match(self, tubes_state: List[List[int]]) -> List[List[int]]:
        """Solve color match puzzle (simplified)."""
        # This is a simplified solver - in production, implement proper puzzle solving
        solution = []
        for tube in tubes_state:
            # Sort colors in each tube
            sorted_tube = sorted(tube, reverse=True)
            solution.append(sorted_tube)
        return solution
    
    def _solve_tube_filling(self, tubes_state: List[List[int]]) -> List[List[int]]:
        """Solve tube filling puzzle (simplified)."""
        # This is a simplified solver - in production, implement proper puzzle solving
        solution = []
        for tube in tubes_state:
            # Sort liquids in each tube
            sorted_tube = sorted(tube, reverse=True)
            solution.append(sorted_tube)
        return solution
    
    async def validate_game_completion(self, game_id: str, submitted_state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate game completion and detect cheating."""
        game = await self.db.games.find_one({"_id": game_id})
        if not game:
            raise ValueError("Game not found")
        
        # Get game state
        game_state = game.get("game_state", {})
        target_state = game_state.get("target_state", [])
        
        # Calculate completion percentage
        completion_percentage = self._calculate_completion_percentage(submitted_state, target_state)
        
        # Check for cheating patterns
        cheat_detection = await self._detect_cheating(game_id, submitted_state)
        
        return {
            "completion_percentage": completion_percentage,
            "is_valid": completion_percentage >= 0,
            "cheat_detected": cheat_detection["detected"],
            "cheat_reason": cheat_detection["reason"]
        }
    
    def _calculate_completion_percentage(self, submitted_state: Dict[str, Any], target_state: List[List[int]]) -> float:
        """Calculate completion percentage based on submitted vs target state."""
        if not submitted_state or not target_state:
            return 0.0
        
        submitted_tubes = submitted_state.get("tubes_state", [])
        if len(submitted_tubes) != len(target_state):
            return 0.0
        
        correct_tubes = 0
        total_tubes = len(target_state)
        
        for i, target_tube in enumerate(target_state):
            if i < len(submitted_tubes) and submitted_tubes[i] == target_tube:
                correct_tubes += 1
        
        return (correct_tubes / total_tubes) * 100
    
    async def _detect_cheating(self, game_id: str, submitted_state: Dict[str, Any]) -> Dict[str, Any]:
        """Detect cheating patterns in game submission."""
        # Get game replay data
        replay = await self.db.replays.find_one({"game_id": game_id})
        if not replay:
            return {"detected": False, "reason": None}
        
        actions = replay.get("action_sequence", [])
        timing_data = replay.get("timing_data", {})
        
        # Check for speed hacks
        if self._detect_speed_hack(timing_data):
            return {"detected": True, "reason": "Speed hack detected"}
        
        # Check for repetitive patterns
        if self._detect_repetitive_patterns(actions):
            return {"detected": True, "reason": "Repetitive pattern detected"}
        
        # Check for unnatural movements
        if self._detect_unnatural_movements(replay.get("mouse_movements", [])):
            return {"detected": True, "reason": "Unnatural movements detected"}
        
        return {"detected": False, "reason": None}
    
    def _detect_speed_hack(self, timing_data: Dict[str, Any]) -> bool:
        """Detect speed hacks based on timing data."""
        # Simplified speed hack detection
        # In production, implement more sophisticated detection
        return False
    
    def _detect_repetitive_patterns(self, actions: List[Dict[str, Any]]) -> bool:
        """Detect repetitive action patterns."""
        # Simplified pattern detection
        # In production, implement more sophisticated detection
        return False
    
    def _detect_unnatural_movements(self, mouse_movements: List[Dict[str, Any]]) -> bool:
        """Detect unnatural mouse movements."""
        # Simplified movement detection
        # In production, implement more sophisticated detection
        return False

game_engine = GameEngine() 