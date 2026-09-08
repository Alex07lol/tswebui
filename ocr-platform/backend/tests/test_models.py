"""Tests for SQLAlchemy ORM models and database tables creation."""
from __future__ import annotations

import uuid
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
        assert isinstance(result.scalars().all(), list)

        # Create a test user with unique email
        test_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=test_email,
            hashed_password="fakehashforphase0",
            full_name="Phase 0 Test User",
            role="admin",
        )
        session.add(user)
        await session.flush()
        assert user.id is not None
        assert len(user.id) == 36

        # Query back
        res = await session.execute(select(User).where(User.email == test_email))
        fetched = res.scalar_one()
        assert fetched.email == test_email
        assert fetched.role == "admin"
