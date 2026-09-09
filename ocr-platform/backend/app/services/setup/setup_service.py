"""Setup service adapter.

Maps consumer-facing 'Setup' abstractions onto the underlying
Configuration and ConfigurationVersion domain models.
"""
from __future__ import annotations

import json
import re
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.configuration import Configuration, ConfigurationVersion


def _slugify(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_\-]+", "-", name.strip().lower())
    cleaned = re.sub(r"^-+|-+$", "", cleaned)
    return cleaned or "setup"


class SetupService:
    @staticmethod
    async def create_setup(
        session: AsyncSession,
        name: str,
        description: str | None = None,
        initial_fields: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        slug = _slugify(name)
        # Check existing slug to guarantee uniqueness
        stmt = select(Configuration).where(Configuration.slug == slug)
        res = await session.execute(stmt)
        if res.scalar_one_or_none():
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"

        config_id = str(uuid.uuid4())
        config = Configuration(
            id=config_id,
            name=name,
            slug=slug,
            description=description or "",
        )
        session.add(config)

        version_id = str(uuid.uuid4())
        fields_data = initial_fields or []
        snapshot = {
            "schema_version": 1,
            "id": slug,
            "name": name,
            "fields": fields_data,
        }

        version = ConfigurationVersion(
            id=version_id,
            configuration_id=config_id,
            version_number=1,
            status="active" if fields_data else "draft",
            config_snapshot=json.dumps(snapshot),
        )
        session.add(version)
        await session.flush()

        return {
            "id": config.id,
            "name": config.name,
            "slug": config.slug,
            "description": config.description,
            "field_count": len(fields_data),
            "status": "ready" if fields_data else "draft",
            "version_id": version.id,
            "version_number": 1,
            "created_at": config.created_at.isoformat() if config.created_at else "",
            "last_scanned": None,
        }

    @staticmethod
    async def list_setups(session: AsyncSession) -> list[dict[str, Any]]:
        stmt = (
            select(Configuration)
            .options(selectinload(Configuration.versions))
            .order_by(Configuration.created_at.desc())
        )
        res = await session.execute(stmt)
        configs = res.scalars().all()

        setups: list[dict[str, Any]] = []
        for c in configs:
            latest_v = None
            if c.versions:
                latest_v = max(c.versions, key=lambda v: v.version_number)

            field_count = 0
            if latest_v and latest_v.config_snapshot:
                try:
                    snap = json.loads(latest_v.config_snapshot)
                    field_count = len(snap.get("fields", []))
                except Exception:
                    field_count = 0

            setups.append({
                "id": c.id,
                "name": c.name,
                "slug": c.slug,
                "description": c.description or "",
                "field_count": field_count,
                "status": "ready" if field_count > 0 else "draft",
                "version_id": latest_v.id if latest_v else None,
                "version_number": latest_v.version_number if latest_v else 1,
                "created_at": c.created_at.isoformat() if c.created_at else "",
                "last_scanned": None,
            })
        return setups

    @staticmethod
    async def get_setup(session: AsyncSession, setup_id: str) -> dict[str, Any] | None:
        stmt = (
            select(Configuration)
            .where(Configuration.id == setup_id)
            .options(selectinload(Configuration.versions))
        )
        res = await session.execute(stmt)
        config = res.scalar_one_or_none()
        if not config:
            return None

        latest_v = max(config.versions, key=lambda v: v.version_number) if config.versions else None
        fields_list: list[dict[str, Any]] = []
        if latest_v and latest_v.config_snapshot:
            try:
                snap = json.loads(latest_v.config_snapshot)
                fields_list = snap.get("fields", [])
            except Exception:
                fields_list = []

        return {
            "id": config.id,
            "name": config.name,
            "slug": config.slug,
            "description": config.description or "",
            "field_count": len(fields_list),
            "status": "ready" if len(fields_list) > 0 else "draft",
            "version_id": latest_v.id if latest_v else None,
            "version_number": latest_v.version_number if latest_v else 1,
            "created_at": config.created_at.isoformat() if config.created_at else "",
            "last_scanned": None,
            "fields": fields_list,
        }

    @staticmethod
    async def update_setup(
        session: AsyncSession, setup_id: str, name: str, description: str | None = None
    ) -> dict[str, Any] | None:
        stmt = select(Configuration).where(Configuration.id == setup_id)
        res = await session.execute(stmt)
        config = res.scalar_one_or_none()
        if not config:
            return None

        config.name = name
        if description is not None:
            config.description = description
        await session.flush()

        return await SetupService.get_setup(session, setup_id)

    @staticmethod
    async def delete_setup(session: AsyncSession, setup_id: str) -> bool:
        stmt = select(Configuration).where(Configuration.id == setup_id)
        res = await session.execute(stmt)
        config = res.scalar_one_or_none()
        if not config:
            return False
        await session.delete(config)
        await session.flush()
        return True
