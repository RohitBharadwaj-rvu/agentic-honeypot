"""
Centralized configuration using Pydantic Settings.
Loads from environment variables and .env file.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    # Upstash Redis
    UPSTASH_REDIS_REST_URL: str
    UPSTASH_REDIS_REST_TOKEN: str
    
    # API Security
    API_SECRET_KEY: str
    
    # OpenRouter API
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # Model Configuration - Using confirmed free tier models
    MODEL_ROLEPLAY: str = "moonshotai/kimi-k2:free"  # For persona engagement
    MODEL_REASONING: str = "moonshotai/kimi-k2:free"  # For detection
    MODEL_FALLBACK: str = "moonshotai/kimi-k2:free"  # Same as fallback
    
    # Debug Mode
    DEBUG: bool = False
    
    # Session Configuration
    SESSION_TTL_SECONDS: int = 3600  # 1 hour as per requirements
    SESSION_KEY_PREFIX: str = "honeypot:session:"
    
    # LRU Cache Fallback Size
    MEMORY_CACHE_MAX_SIZE: int = 1000


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
