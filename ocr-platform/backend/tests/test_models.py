"""Tests for SQLAlchemy ORM models and database tables creation."""
from __future__ import annotations

import pytest
from sqlalchemy import select

from app.core.database import AsyncSessionLocal, create_all_tables
from app.models import (
    AuditLog,
    Configuration,
    ConfigurationVersion,
    Dataset,
    Document,
    OCRJob,
    OCRResult,
    User,
)


@pytest.mark.anyio
async def test_database_tables_create_and_query() -> None:
    """All tables can be created and queried cleanly."""
    await create_all_tables()

    async with AsyncSessionLocal() as session:
        # Verify query against users table
        result = await session.execute(select(User))
        assert result.scalars().all() == []

        # Create a test user
        user = User(
            email="test@example.com",
            hashed_password="fakehashforphase0",
            full_name="Phase 0 Test User",
            role="admin",
        )
        session.add(user)
        await session.flush()
        assert user.id is not None
        assert len(user.id) == 36

        # Query back
        res = await session.execute(select(User).where(User.email == "test@example.com"))
        fetched = res.scalar_one()
        assert fetched.email == "test@example.com"
        assert fetched.role == "admin"
