from pydantic_settings import BaseSettings
from typing import List
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    # Database Configuration
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017/gaming_platform")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    mongodb_db_name: str = os.getenv("MONGODB_DB_NAME", "gaming_platform")
    
    # Security Configuration
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    aes_key: str = os.getenv("AES_KEY", "your-32-byte-aes-key-for-encryption")
    salt: str = os.getenv("SALT", "your-salt-for-encryption")
    
    
    mail_username: str = os.getenv("MAIL_USERNAME", "")
    mail_password: str = os.getenv("MAIL_PASSWORD", "")
    mail_from: str = os.getenv("MAIL_FROM", "")
    mail_port: int = int(os.getenv("MAIL_PORT", "587"))
    mail_server: str = os.getenv("MAIL_SERVER", "")
    mail_tls: bool = os.getenv("MAIL_TLS", "true").lower() == "true"
    mail_ssl: bool = os.getenv("MAIL_SSL", "false").lower() == "true"
    
    # Cookie Configuration
    cookie_domain: str = os.getenv("COOKIE_DOMAIN", "localhost")
    cookie_secure: bool = os.getenv("COOKIE_SECURE", "False").lower() == "true"
    cookie_httponly: bool = os.getenv("COOKIE_HTTPONLY", "True").lower() == "true"
    cookie_samesite: str = os.getenv("COOKIE_SAMESITE", "lax")
    access_token_cookie_name: str = os.getenv("ACCESS_TOKEN_COOKIE_NAME", "access_token")
    refresh_token_cookie_name: str = os.getenv("REFRESH_TOKEN_COOKIE_NAME", "refresh_token")

    # 1inch API Configuration
    oneinch_api_url: str = os.getenv("ONEINCH_API_URL", "https://api.1inch.dev")
    oneinch_api_key: str = os.getenv("ONEINCH_API_KEY", "")

    # Game Configuration
    default_game_timer: int = int(os.getenv("DEFAULT_GAME_TIMER", "60"))
    default_entry_cost: int = int(os.getenv("DEFAULT_ENTRY_COST", "100"))
    default_reward_multiplier: float = float(os.getenv("DEFAULT_REWARD_MULTIPLIER", "1.5"))

    # Server Configuration
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # CORS Configuration
    allowed_origins: List[str] = ["*"]

    # Celery Configuration
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

    class Config:
        env_file = ".env"

settings = Settings()
