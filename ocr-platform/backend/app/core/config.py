"""Application configuration using Pydantic BaseSettings."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    _HAS_V2_SETTINGS = True
except ImportError:
    from pydantic import BaseSettings  # type: ignore[no-redef]
    _HAS_V2_SETTINGS = False

from pydantic import Field


if _HAS_V2_SETTINGS:
    from pydantic import field_validator

    class Settings(BaseSettings):
        """Central application settings loaded from environment variables."""

        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore",
        )

        app_name: str = "OCR Platform"
        app_version: str = "0.1.0"
        debug: bool = False
        environment: Literal["development", "production", "testing"] = "development"

        host: str = "0.0.0.0"
        port: int = 8000
        allowed_origins: list[str] = Field(
            default=["http://localhost:5173", "http://localhost:3000"]
        )

        database_url: str = "sqlite+aiosqlite:///./ocr_platform.db"
        redis_url: str = "redis://localhost:6379/0"

        secret_key: str = "CHANGE_ME_IN_PRODUCTION_USE_LONG_RANDOM_KEY"
        algorithm: str = "HS256"
        access_token_expire_minutes: int = 60 * 24

        storage_backend: Literal["local", "s3"] = "local"
        local_storage_path: Path = Path("./storage")
        max_upload_size_mb: int = 50

        default_ocr_provider: str = "tesseract"
        tesseract_cmd: str = "tesseract"
        default_ocr_language: str = "eng"

        job_backend: Literal["inline", "celery"] = "inline"
        worker_concurrency: int = 2

        log_level: str = "INFO"
        log_format: Literal["json", "console"] = "console"
        require_admin_auth: bool = True

        @field_validator("local_storage_path")
        @classmethod
        def ensure_storage_path(cls, v: Path) -> Path:
            v.mkdir(parents=True, exist_ok=True)
            return v

else:
    from pydantic import validator

    class Settings(BaseSettings):  # type: ignore[no-redef]
        """Central application settings loaded from environment variables (Pydantic v1)."""

        app_name: str = "OCR Platform"
        app_version: str = "0.1.0"
        debug: bool = False
        environment: str = "development"

        host: str = "0.0.0.0"
        port: int = 8000
        allowed_origins: list[str] = Field(
            default=["http://localhost:5173", "http://localhost:3000"]
        )

        database_url: str = "sqlite+aiosqlite:///./ocr_platform.db"
        redis_url: str = "redis://localhost:6379/0"

        secret_key: str = "CHANGE_ME_IN_PRODUCTION_USE_LONG_RANDOM_KEY"
        algorithm: str = "HS256"
        access_token_expire_minutes: int = 60 * 24

        storage_backend: str = "local"
        local_storage_path: Path = Path("./storage")
        max_upload_size_mb: int = 50

        default_ocr_provider: str = "tesseract"
        tesseract_cmd: str = "tesseract"
        default_ocr_language: str = "eng"

        job_backend: str = "inline"
        worker_concurrency: int = 2

        log_level: str = "INFO"
        log_format: str = "console"
        require_admin_auth: bool = True

        class Config:
            env_file = ".env"
            case_sensitive = False
            extra = "ignore"

        @validator("local_storage_path", pre=True, always=True)
        def ensure_storage_path(cls, v: Path | str) -> Path:
            p = Path(v) if isinstance(v, str) else v
            p.mkdir(parents=True, exist_ok=True)
            return p


# Singleton instance
settings = Settings()
