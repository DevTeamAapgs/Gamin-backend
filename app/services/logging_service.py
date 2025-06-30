from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.db.mongo import get_database
from app.models.logging import RequestLog, SecurityLog, GameActionLog
import logging
import json

logger = logging.getLogger(__name__)

class LoggingService:
    def __init__(self):
        pass  # Remove db initialization from __init__
    
    async def log_request(self, request_data: Dict[str, Any]) -> bool:
        """Log HTTP request to database."""
        try:
            # Get database connection
            db = get_database()
            if db is None:
                logger.warning("Database connection not available for request logging")
                return False
            
            # Create request log entry
            request_log = RequestLog(
                method=request_data.get("method", ""),
                path=request_data.get("path", ""),
                status_code=request_data.get("status_code", 0),
                client_ip=request_data.get("client_ip", ""),
                user_agent=request_data.get("user_agent", ""),
                device_fingerprint=request_data.get("device_fingerprint", ""),
                player_id=request_data.get("player_id"),
                request_headers=request_data.get("request_headers", {}),
                response_headers=request_data.get("response_headers", {}),
                request_body=request_data.get("request_body"),
                response_body=request_data.get("response_body"),
                process_time=request_data.get("process_time", 0.0),
                error_message=request_data.get("error_message"),
                ttl=datetime.utcnow() + timedelta(days=30)  # Keep logs for 30 days
            )
            
            # Save to database
            await db.request_logs.insert_one(request_log.dict(by_alias=True))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log request to database: {e}")
            return False
    
    async def log_security_event(self, event_data: Dict[str, Any]) -> bool:
        """Log security event to database."""
        try:
            # Get database connection
            db = get_database()
            if db is None:
                logger.warning("Database connection not available for security event logging")
                return False
            
            # Create security log entry
            security_log = SecurityLog(
                event_type=event_data.get("event_type", ""),
                player_id=event_data.get("player_id"),
                client_ip=event_data.get("client_ip", ""),
                device_fingerprint=event_data.get("device_fingerprint", ""),
                user_agent=event_data.get("user_agent", ""),
                details=event_data.get("details", {}),
                severity=event_data.get("severity", "info"),
                ttl=datetime.utcnow() + timedelta(days=90)  # Keep security logs for 90 days
            )
            
            # Save to database
            await db.security_logs.insert_one(security_log.dict(by_alias=True))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log security event to database: {e}")
            return False
    
    async def log_game_action(self, action_data: Dict[str, Any]) -> bool:
        """Log game action to database."""
        try:
            # Get database connection
            db = get_database()
            if db is None:
                logger.warning("Database connection not available for game action logging")
                return False
            
            # Create game action log entry
            game_action_log = GameActionLog(
                game_id=action_data.get("game_id"),
                player_id=action_data.get("player_id"),
                action_type=action_data.get("action_type", ""),
                action_data=action_data.get("action_data", {}),
                session_id=action_data.get("session_id"),
                client_ip=action_data.get("client_ip", ""),
                device_fingerprint=action_data.get("device_fingerprint", "")
            )
            
            # Save to database
            await db.game_action_logs.insert_one(game_action_log.dict(by_alias=True))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log game action to database: {e}")
            return False
    
    async def get_request_logs(
        self,
        player_id: Optional[str] = None,
        path: Optional[str] = None,
        status_code: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list:
        """Get request logs with optional filtering."""
        try:
            # Get database connection
            db = get_database()
            if db is None:
                logger.warning("Database connection not available for getting request logs")
                return []
            
            # Build query
            query = {}
            if player_id:
                query["player_id"] = player_id
            if path:
                query["path"] = {"$regex": path, "$options": "i"}
            if status_code:
                query["status_code"] = status_code
            if start_date or end_date:
                query["created_at"] = {}
                if start_date:
                    query["created_at"]["$gte"] = start_date
                if end_date:
                    query["created_at"]["$lte"] = end_date
            
            # Get logs
            logs = await db.request_logs.find(query).sort("created_at", -1).limit(limit).to_list(length=limit)
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get request logs: {e}")
            return []
    
    async def get_security_logs(
        self,
        event_type: Optional[str] = None,
        player_id: Optional[str] = None,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list:
        """Get security logs with optional filtering."""
        try:
            # Get database connection
            db = get_database()
            if db is None:
                logger.warning("Database connection not available for getting security logs")
                return []
            
            # Build query
            query = {}
            if event_type:
                query["event_type"] = event_type
            if player_id:
                query["player_id"] = player_id
            if severity:
                query["severity"] = severity
            if start_date or end_date:
                query["created_at"] = {}
                if start_date:
                    query["created_at"]["$gte"] = start_date
                if end_date:
                    query["created_at"]["$lte"] = end_date
            
            # Get logs
            logs = await db.security_logs.find(query).sort("created_at", -1).limit(limit).to_list(length=limit)
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get security logs: {e}")
            return []
    
    async def get_game_action_logs(
        self,
        game_id: Optional[str] = None,
        player_id: Optional[str] = None,
        action_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list:
        """Get game action logs with optional filtering."""
        try:
            # Get database connection
            db = get_database()
            if db is None:
                logger.warning("Database connection not available for getting game action logs")
                return []
            
            # Build query
            query = {}
            if game_id:
                query["game_id"] = game_id
            if player_id:
                query["player_id"] = player_id
            if action_type:
                query["action_type"] = action_type
            if start_date or end_date:
                query["created_at"] = {}
                if start_date:
                    query["created_at"]["$gte"] = start_date
                if end_date:
                    query["created_at"]["$lte"] = end_date
            
            # Get logs
            logs = await db.game_action_logs.find(query).sort("created_at", -1).limit(limit).to_list(length=limit)
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get game action logs: {e}")
            return []
    
    async def cleanup_old_logs(self) -> Dict[str, Any]:
        """Clean up old logs based on TTL."""
        try:
            # Get database connection
            db = get_database()
            if db is None:
                logger.warning("Database connection not available for cleanup")
                return {"error": "Database connection not available"}
            
            current_time = datetime.utcnow()
            
            # Clean up request logs
            request_result = await db.request_logs.delete_many({
                "ttl": {"$lt": current_time}
            })
            
            # Clean up security logs
            security_result = await db.security_logs.delete_many({
                "ttl": {"$lt": current_time}
            })
            
            # Clean up game action logs (keep for 7 days)
            game_action_result = await db.game_action_logs.delete_many({
                "created_at": {"$lt": current_time - timedelta(days=7)}
            })
            
            return {
                "request_logs_deleted": request_result.deleted_count,
                "security_logs_deleted": security_result.deleted_count,
                "game_action_logs_deleted": game_action_result.deleted_count
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
            return {"error": str(e)}
    
    async def get_log_statistics(self) -> Dict[str, Any]:
        """Get logging statistics."""
        try:
            # Get database connection
            db = get_database()
            if db is None:
                logger.warning("Database connection not available for statistics")
                return {"error": "Database connection not available"}
            
            # Get counts
            total_requests = await db.request_logs.count_documents({})
            total_security_events = await db.security_logs.count_documents({})
            total_game_actions = await db.game_action_logs.count_documents({})
            
            # Get recent activity (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(days=1)
            
            recent_requests = await db.request_logs.count_documents({
                "created_at": {"$gte": yesterday}
            })
            
            recent_security_events = await db.security_logs.count_documents({
                "created_at": {"$gte": yesterday}
            })
            
            recent_game_actions = await db.game_action_logs.count_documents({
                "created_at": {"$gte": yesterday}
            })
            
            # Get error rates
            error_requests = await db.request_logs.count_documents({
                "status_code": {"$gte": 400}
            })
            
            critical_security_events = await db.security_logs.count_documents({
                "severity": "critical"
            })
            
            return {
                "total_requests": total_requests,
                "total_security_events": total_security_events,
                "total_game_actions": total_game_actions,
                "recent_requests_24h": recent_requests,
                "recent_security_events_24h": recent_security_events,
                "recent_game_actions_24h": recent_game_actions,
                "error_rate": (error_requests / total_requests * 100) if total_requests > 0 else 0,
                "critical_security_events": critical_security_events
            }
            
        except Exception as e:
            logger.error(f"Failed to get log statistics: {e}")
            return {"error": str(e)}

logging_service = LoggingService() 