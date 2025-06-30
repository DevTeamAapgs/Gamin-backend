from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.db.mongo import get_database
import logging
import json

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        self.db = get_database()
    
    async def track_game_action(self, game_id: str, player_id: str, action_data: Dict[str, Any]):
        """Track individual game action for analytics."""
        try:
            analytics_data = {
                "game_id": game_id,
                "player_id": player_id,
                "action_type": action_data.get("type"),
                "timestamp": datetime.utcnow(),
                "position": action_data.get("position"),
                "duration": action_data.get("duration"),
                "success": action_data.get("success", False),
                "metadata": action_data.get("metadata", {})
            }
            
            await self.db.game_analytics.insert_one(analytics_data)
            
        except Exception as e:
            logger.error(f"Failed to track game action: {e}")
    
    async def generate_heatmap_data(self, game_type: str, level: int, time_range: str = "24h") -> Dict[str, Any]:
        """Generate heatmap data for game interactions."""
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            if time_range == "24h":
                start_time = end_time - timedelta(hours=24)
            elif time_range == "7d":
                start_time = end_time - timedelta(days=7)
            elif time_range == "30d":
                start_time = end_time - timedelta(days=30)
            else:
                start_time = end_time - timedelta(hours=24)
            
            # Aggregate click positions
            pipeline = [
                {
                    "$match": {
                        "game_type": game_type,
                        "level": level,
                        "timestamp": {"$gte": start_time, "$lte": end_time}
                    }
                },
                {
                    "$group": {
                        "_id": "$position",
                        "count": {"$sum": 1},
                        "avg_duration": {"$avg": "$duration"},
                        "success_rate": {"$avg": {"$cond": ["$success", 1, 0]}}
                    }
                },
                {
                    "$sort": {"count": -1}
                }
            ]
            
            heatmap_data = await self.db.game_analytics.aggregate(pipeline).to_list(length=1000)
            
            return {
                "game_type": game_type,
                "level": level,
                "time_range": time_range,
                "data_points": len(heatmap_data),
                "heatmap": heatmap_data
            }
            
        except Exception as e:
            logger.error(f"Failed to generate heatmap data: {e}")
            return {"error": str(e)}
    
    async def get_player_analytics(self, player_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for a player."""
        try:
            # Get player's game history
            games = await self.db.games.find({"player_id": player_id}).to_list(length=1000)
            
            if not games:
                return {"error": "No games found for player"}
            
            # Calculate basic stats
            total_games = len(games)
            completed_games = len([g for g in games if g.get("status") == "completed"])
            avg_completion = sum(g.get("completion_percentage", 0) for g in games) / total_games
            
            # Calculate time-based patterns
            time_patterns = await self._analyze_time_patterns(player_id)
            
            # Calculate difficulty progression
            difficulty_progression = await self._analyze_difficulty_progression(player_id)
            
            # Calculate retry patterns
            retry_patterns = await self._analyze_retry_patterns(player_id)
            
            return {
                "player_id": player_id,
                "total_games": total_games,
                "completed_games": completed_games,
                "completion_rate": completed_games / total_games if total_games > 0 else 0,
                "average_completion": avg_completion,
                "time_patterns": time_patterns,
                "difficulty_progression": difficulty_progression,
                "retry_patterns": retry_patterns
            }
            
        except Exception as e:
            logger.error(f"Failed to get player analytics: {e}")
            return {"error": str(e)}
    
    async def _analyze_time_patterns(self, player_id: str) -> Dict[str, Any]:
        """Analyze player's time-based gaming patterns."""
        try:
            # Get games with timestamps
            games = await self.db.games.find(
                {"player_id": player_id},
                {"start_time": 1, "end_time": 1, "completion_percentage": 1}
            ).to_list(length=1000)
            
            if not games:
                return {}
            
            # Analyze hour distribution
            hour_distribution = {}
            for game in games:
                start_time = game.get("start_time")
                if start_time:
                    hour = start_time.hour
                    hour_distribution[hour] = hour_distribution.get(hour, 0) + 1
            
            # Analyze session duration
            session_durations = []
            for game in games:
                start_time = game.get("start_time")
                end_time = game.get("end_time")
                if start_time and end_time:
                    duration = (end_time - start_time).total_seconds()
                    session_durations.append(duration)
            
            avg_session_duration = sum(session_durations) / len(session_durations) if session_durations else 0
            
            return {
                "hour_distribution": hour_distribution,
                "average_session_duration": avg_session_duration,
                "total_sessions": len(session_durations)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze time patterns: {e}")
            return {}
    
    async def _analyze_difficulty_progression(self, player_id: str) -> Dict[str, Any]:
        """Analyze player's difficulty progression."""
        try:
            # Get games ordered by time
            games = await self.db.games.find(
                {"player_id": player_id},
                {"level": 1, "completion_percentage": 1, "created_at": 1}
            ).sort("created_at", 1).to_list(length=1000)
            
            if not games:
                return {}
            
            # Calculate progression metrics
            level_progression = {}
            for game in games:
                level = game.get("level", 1)
                completion = game.get("completion_percentage", 0)
                
                if level not in level_progression:
                    level_progression[level] = []
                level_progression[level].append(completion)
            
            # Calculate average completion per level
            avg_completion_by_level = {}
            for level, completions in level_progression.items():
                avg_completion_by_level[level] = sum(completions) / len(completions)
            
            return {
                "level_progression": level_progression,
                "average_completion_by_level": avg_completion_by_level,
                "max_level_reached": max(level_progression.keys()) if level_progression else 1
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze difficulty progression: {e}")
            return {}
    
    async def _analyze_retry_patterns(self, player_id: str) -> Dict[str, Any]:
        """Analyze player's retry patterns."""
        try:
            # Get game attempts
            attempts = await self.db.game_attempts.find(
                {"player_id": player_id}
            ).to_list(length=1000)
            
            if not attempts:
                return {}
            
            # Group attempts by game
            game_attempts = {}
            for attempt in attempts:
                game_id = attempt.get("game_id")
                if game_id not in game_attempts:
                    game_attempts[game_id] = []
                game_attempts[game_id].append(attempt)
            
            # Calculate retry statistics
            retry_counts = [len(attempts) for attempts in game_attempts.values()]
            avg_retries = sum(retry_counts) / len(retry_counts) if retry_counts else 0
            max_retries = max(retry_counts) if retry_counts else 0
            
            # Analyze retry success patterns
            retry_success_patterns = {}
            for game_id, attempts in game_attempts.items():
                for i, attempt in enumerate(attempts):
                    attempt_number = i + 1
                    completion = attempt.get("completion_percentage", 0)
                    
                    if attempt_number not in retry_success_patterns:
                        retry_success_patterns[attempt_number] = []
                    retry_success_patterns[attempt_number].append(completion)
            
            # Calculate average completion per attempt number
            avg_completion_by_attempt = {}
            for attempt_num, completions in retry_success_patterns.items():
                avg_completion_by_attempt[attempt_num] = sum(completions) / len(completions)
            
            return {
                "average_retries_per_game": avg_retries,
                "max_retries": max_retries,
                "retry_success_patterns": retry_success_patterns,
                "average_completion_by_attempt": avg_completion_by_attempt
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze retry patterns: {e}")
            return {}
    
    async def get_platform_analytics(self) -> Dict[str, Any]:
        """Get platform-wide analytics."""
        try:
            # Get basic platform stats
            total_players = await self.db.players.count_documents({})
            total_games = await self.db.games.count_documents({})
            active_players_24h = await self.db.games.count_documents({
                "start_time": {"$gte": datetime.utcnow() - timedelta(hours=24)}
            })
            
            # Get revenue analytics
            total_revenue = await self.db.transactions.aggregate([
                {"$match": {"transaction_type": "game_entry"}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]).to_list(length=1)
            
            total_revenue = total_revenue[0]["total"] if total_revenue else 0
            
            # Get game type distribution
            game_type_distribution = await self.db.games.aggregate([
                {"$group": {"_id": "$game_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]).to_list(length=10)
            
            return {
                "total_players": total_players,
                "total_games": total_games,
                "active_players_24h": active_players_24h,
                "total_revenue": total_revenue,
                "game_type_distribution": game_type_distribution
            }
            
        except Exception as e:
            logger.error(f"Failed to get platform analytics: {e}")
            return {"error": str(e)}

analytics_service = AnalyticsService() 