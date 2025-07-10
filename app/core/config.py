import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator

class Settings(BaseSettings):
    # Database Configuration
    mongodb_url: str = "mongodb://192.168.1.54:27017/gaming_platform"
    redis_url: str = "redis://localhost:6379"
    mongodb_db_name: str = "gaming_platform"
    
    # Security Configuration
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    aes_key: str = "your-32-byte-aes-key-for-encryption"
    salt: str = "your-salt-for-encryption"
    
    # Email Configuration
    mail_username: str = "smtp@mailtrap.io"
    mail_password: str = "95beec87707cc59f2f2dc215a6691234"
    mail_from: str = "noreply@keepwisely.com"
    mail_port: int = 587
    mail_server: str = "smtp.mailtrap.io"
    mail_tls: bool = True
    mail_ssl: bool = False
    
    # Cookie Configuration
    cookie_domain: str = "localhost"
    cookie_secure: bool = False
    cookie_httponly: bool = True
    cookie_samesite: str = "lax"
    access_token_cookie_name: str = "access_token"
    refresh_token_cookie_name: str = "refresh_token"
    
    # 1inch API Configuration
    oneinch_api_url: str = "https://api.1inch.dev"
    oneinch_api_key: str = "your-1inch-api-key"
    
    # Game Configuration
    default_game_timer: int = 60
    default_entry_cost: int = 100
    default_reward_multiplier: float = 1.5
    
    # Admin Configuration
    admin_username: str = "admin"
    admin_password: str = "admin-secure-password"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # CORS Configuration
    allowed_origins: List[str] = ["*"]
    
    @validator('allowed_origins', pre=True)
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()