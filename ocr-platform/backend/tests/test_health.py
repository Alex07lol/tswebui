"""Tests for the /api/health endpoint."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_health_check(client: AsyncClient) -> None:
    """The health endpoint must return 200 and valid JSON."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "ocr_providers" in data
    assert "tesseract" in data["ocr_providers"]
