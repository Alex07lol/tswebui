"""Application configuration using pydantic-settings."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "OCR Platform"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "production", "testing"] = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"]
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./ocr_platform.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT Auth
    secret_key: str = "CHANGE_ME_IN_PRODUCTION_USE_LONG_RANDOM_KEY"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Storage
    storage_backend: Literal["local", "s3"] = "local"
    local_storage_path: Path = Path("./storage")
    max_upload_size_mb: int = 50

    # OCR
    default_ocr_provider: str = "tesseract"
    tesseract_cmd: str = "tesseract"
    default_ocr_language: str = "eng"

    # Jobs
    job_backend: Literal["inline", "celery"] = "inline"
    worker_concurrency: int = 2

    # Logging
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "console"

    @field_validator("local_storage_path")
    @classmethod
    def ensure_storage_path(cls, v: Path) -> Path:
        """Ensure local storage directory exists on startup."""
        v.mkdir(parents=True, exist_ok=True)
        return v


# Singleton — import this everywhere
settings = Settings()
