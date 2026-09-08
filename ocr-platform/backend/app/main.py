"""FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import create_all_tables
from app.core.logging import configure_logging, get_logger
from app.providers.ocr.registry import list_providers, register_provider
from app.services.ocr.tesseract import TesseractProvider

log = get_logger(__name__)


def _register_providers() -> None:
    """Register all built-in providers."""
    if "tesseract" not in list_providers():
        register_provider(TesseractProvider())


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle."""
    configure_logging(log_level=settings.log_level, log_format=settings.log_format)
    log.info(
        "Starting OCR Platform",
        version=settings.app_version,
        environment=settings.environment,
        debug=settings.debug,
    )

    if settings.environment in ("development", "testing"):
        await create_all_tables()
        log.info("Database tables ensured")

    _register_providers()
    log.info("Registered OCR providers", providers=list_providers())

    yield

    log.info("Shutting down OCR Platform")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    _register_providers()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Attach all API routers
    from app.api import configurations, discovery, documents, extraction, health, ocr

    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
    app.include_router(ocr.router, prefix="/api/ocr", tags=["ocr"])
    app.include_router(configurations.router, prefix="/api/configurations", tags=["configurations"])
    app.include_router(extraction.router, prefix="/api/extraction", tags=["extraction"])
    app.include_router(discovery.router, prefix="/api", tags=["discovery"])

    return app


app = create_app()
