"""Pytest configuration and shared fixtures."""
from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient

# Set testing environment variables before importing app
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_ocr_platform.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-testing-only-12345678"
os.environ["LOG_LEVEL"] = "WARNING"


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncClient:
    """Async test client for FastAPI."""
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
