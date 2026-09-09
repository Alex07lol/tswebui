"""Database engine and session factory."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Create the async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all SQLAlchemy ORM models."""

    type_annotation_map: dict[Any, Any] = {}


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides a database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_all_tables() -> None:
    """Create all tables and ensure schema columns (used in development/testing). Production uses Alembic."""
    import app.models  # noqa: F401 - Ensure all models are registered on Base.metadata
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Migrate new columns on existing SQLite tables safely
        def _migrate(sync_conn):
            new_cols = [
                ("websites", "published_version_id", "VARCHAR(36)"),
                ("website_versions", "bindings_json", "TEXT"),
                ("website_versions", "actions_json", "TEXT"),
                ("website_versions", "conditions_json", "TEXT"),
                ("website_versions", "computed_fields_json", "TEXT"),
                ("website_pages", "components_json", "TEXT"),
            ]
            for tbl, col, col_type in new_cols:
                try:
                    res = sync_conn.exec_driver_sql(f"PRAGMA table_info({tbl})").fetchall()
                    existing = [r[1] for r in res]
                    if existing and col not in existing:
                        sync_conn.exec_driver_sql(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_type}")
                except Exception:
                    pass

        await conn.run_sync(_migrate)
