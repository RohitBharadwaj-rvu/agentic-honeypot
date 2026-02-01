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
    
    # NVIDIA API (replaces OpenRouter)
    NVIDIA_API_KEY: str = ""  # Set via environment variable or .env file
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    
    # Model Configuration - Using NVIDIA API with Kimi K2
    MODEL_PRIMARY: str = "moonshotai/kimi-k2-instruct-0905"
    MODEL_FALLBACK: str = "moonshotai/kimi-k2-instruct-0905"
    
    # Debug Mode
    DEBUG: bool = False
    
    # Session Configuration
    SESSION_TTL_SECONDS: int = 3600  # 1 hour as per requirements
    SESSION_KEY_PREFIX: str = "honeypot:session:"
    
    # LRU Cache Fallback Size
    MEMORY_CACHE_MAX_SIZE: int = 1000
    
    # Persona Configuration
    PERSONA_NAME: str = "Ramesh Kumar"
    PERSONA_AGE: int = 67
    PERSONA_BACKGROUND: str = "retired government employee"
    PERSONA_LOCATION: str = "Pune"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
