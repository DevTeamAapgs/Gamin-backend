import uuid
import hashlib
import secrets
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import string

def generate_uuid() -> str:
    """Generate a unique UUID string."""
    return str(uuid.uuid4())

def generate_device_fingerprint(user_agent: str, screen_res: str, timezone: str) -> str:
    """Generate a device fingerprint from browser data."""
    fingerprint_data = {
        "user_agent": user_agent,
        "screen_resolution": screen_res,
        "timezone": timezone,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()

def hash_string(text: str) -> str:
    """Hash a string using SHA-256."""
    return hashlib.sha256(text.encode()).hexdigest()

def generate_random_token(length: int = 32) -> str:
    """Generate a random token of specified length."""
    return secrets.token_urlsafe(length)

def encode_base64(data: bytes) -> str:
    """Encode bytes to base64 string."""
    return base64.b64encode(data).decode('utf-8')

def decode_base64(data: str) -> bytes:
    """Decode base64 string to bytes."""
    return base64.b64decode(data.encode('utf-8'))

def validate_wallet_address(address: str) -> bool:
    """Validate Ethereum wallet address format."""
    if not address or not isinstance(address, str):
        return False
    
    # Basic Ethereum address validation
    if not address.startswith('0x'):
        return False
    
    if len(address) != 42:  # 0x + 40 hex characters
        return False
    
    try:
        int(address[2:], 16)  # Check if it's valid hex
        return True
    except ValueError:
        return False

def calculate_completion_percentage(completed: int, total: int) -> float:
    """Calculate completion percentage."""
    if total == 0:
        return 0.0
    return round((completed / total) * 100, 2)

def format_timestamp(timestamp: datetime) -> str:
    """Format timestamp to ISO string."""
    return timestamp.isoformat()

def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO timestamp string to datetime."""
    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

def is_token_expired(expires_at: datetime) -> bool:
    """Check if token is expired."""
    return datetime.utcnow() > expires_at

def get_time_until_expiry(expires_at: datetime) -> timedelta:
    """Get time until token expires."""
    return expires_at - datetime.utcnow()

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '{', '}']
    sanitized = text
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized.strip()

def validate_email(email: str) -> bool:
    """Basic email validation."""
    if not email or not isinstance(email, str):
        return False
    
    # Basic email format check
    if '@' not in email or '.' not in email:
        return False
    
    if email.count('@') != 1:
        return False
    
    parts = email.split('@')
    if len(parts) != 2:
        return False
    
    local, domain = parts
    if not local or not domain:
        return False
    
    if '.' not in domain:
        return False
    
    return True

def generate_game_id() -> str:
    """Generate a unique game ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_part = secrets.token_hex(4)
    return f"game_{timestamp}_{random_part}"

def calculate_reward_multiplier(completion_percentage: float) -> float:
    """Calculate reward multiplier based on completion percentage."""
    if completion_percentage >= 95:
        return 2.0
    elif completion_percentage >= 85:
        return 1.5
    elif completion_percentage >= 70:
        return 1.2
    elif completion_percentage >= 50:
        return 0.8
    else:
        return 0.3

def format_currency(amount: float, currency: str = "TOKEN") -> str:
    """Format currency amount."""
    return f"{amount:.2f} {currency}"

def validate_game_data(game_data: Dict[str, Any]) -> bool:
    """Validate game submission data."""
    required_fields = ['game_id', 'completion_percentage']
    
    for field in required_fields:
        if field not in game_data:
            return False
    
    # Validate completion percentage
    completion = game_data.get('completion_percentage')
    if not isinstance(completion, (int, float)) or completion < 0 or completion > 100:
        return False
    
    return True

def generate_session_id() -> str:
    """Generate a unique session ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_part = secrets.token_hex(8)
    return f"session_{timestamp}_{random_part}"

def mask_wallet_address(address: str) -> str:
    """Mask wallet address for display (show first and last 4 characters)."""
    if not address or len(address) < 8:
        return address
    
    return f"{address[:6]}...{address[-4:]}"

def calculate_difficulty_score(level: int, attempts: int, avg_completion: float) -> float:
    """Calculate adaptive difficulty score."""
    base_difficulty = level * 0.5
    attempt_penalty = attempts * 0.1
    performance_bonus = max(0, (avg_completion - 50) * 0.01)
    
    return max(1.0, base_difficulty + attempt_penalty - performance_bonus)

def is_valid_username(username: str) -> bool:
    """Validate username format."""
    if not username or not isinstance(username, str):
        return False
    
    # Username should be 3-20 characters, alphanumeric and underscores only
    if len(username) < 3 or len(username) > 20:
        return False
    
    import re
    pattern = r'^[a-zA-Z0-9_]+$'
    return bool(re.match(pattern, username))

def generate_heatmap_key(x: int, y: int, grid_size: int = 10) -> str:
    """Generate a key for heatmap data based on coordinates."""
    grid_x = x // grid_size
    grid_y = y // grid_size
    return f"{grid_x}_{grid_y}"

def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate Euclidean distance between two points."""
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

def detect_unnatural_movement(movements: list, threshold: float = 1000) -> bool:
    """Detect unnatural mouse movements (simplified)."""
    if len(movements) < 2:
        return False
    
    total_distance = 0
    for i in range(1, len(movements)):
        prev = movements[i-1]
        curr = movements[i]
        
        distance = calculate_distance(
            prev.get('x', 0), prev.get('y', 0),
            curr.get('x', 0), curr.get('y', 0)
        )
        total_distance += distance
    
    # If total distance is too high for the number of movements, it might be unnatural
    avg_distance = total_distance / (len(movements) - 1)
    return avg_distance > threshold

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def validate_ip_address(ip: str) -> bool:
    """Basic IP address validation."""
    if not ip or not isinstance(ip, str):
        return False
    
    # Basic IPv4 validation
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    
    try:
        for part in parts:
            num = int(part)
            if num < 0 or num > 255:
                return False
        return True
    except ValueError:
        return False

def generate_unique_wallet_address() -> str:
    """
    Generate a unique Ethereum-style wallet address.
    
    Returns:
        str: A unique wallet address in the format 0x + 40 hex characters
    """
    # Generate 40 random hex characters (20 bytes)
    hex_chars = string.hexdigits.lower()[:16]  # 0-9, a-f
    wallet_hex = ''.join(secrets.choice(hex_chars) for _ in range(40))
    
    # Return in Ethereum address format
    return f"0x{wallet_hex}"

def generate_secure_token(length: int = 32) -> str:
    """
    Generate a secure random token.
    
    Args:
        length (int): Length of the token in characters
        
    Returns:
        str: A secure random token
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length)) 