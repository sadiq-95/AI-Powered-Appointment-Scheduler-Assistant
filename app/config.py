"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    gemini_api_key: str = ""
    gemini_model_name: str = "gemini-1.5-flash-lite"
    tz: str = "Asia/Kolkata"
    
    # Confidence thresholds
    ocr_min_confidence: float = 0.5
    extraction_min_confidence: float = 0.6
    normalization_min_confidence: float = 0.7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
