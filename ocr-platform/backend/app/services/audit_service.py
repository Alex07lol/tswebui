"""Audit logging service for tracking system events."""
from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.audit import AuditLog

log = get_logger(__name__)


class AuditService:
    """Records audit logs for compliance, security, and traceability."""

    @staticmethod
    async def log_event(
        session: AsyncSession,
        event_type: str,
        actor_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        request_id: str | None = None,
    ) -> AuditLog:
        """Create and persist an immutable audit log entry."""
        entry = AuditLog(
            id=str(uuid.uuid4()),
            event_type=event_type,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details_json=json.dumps(details) if details else None,
            ip_address=ip_address,
            request_id=request_id,
        )
        session.add(entry)
        await session.flush()
        log.info(
            "Audit event logged",
            event_type=event_type,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
        )
        return entry
