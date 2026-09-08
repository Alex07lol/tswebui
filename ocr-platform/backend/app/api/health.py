"""Health check and system status endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.providers.ocr.registry import list_providers

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    ocr_providers: list[str]


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return the application health status and registered OCR providers."""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.environment,
        ocr_providers=list_providers(),
    )
