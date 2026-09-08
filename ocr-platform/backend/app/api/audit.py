"""Audit log API endpoints."""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.audit import AuditLog

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: str
    event_type: str
    actor_id: str | None
    resource_type: str | None
    resource_id: str | None
    details: dict[str, Any] | None
    ip_address: str | None
    request_id: str | None
    created_at: Any

    class Config:
        orm_mode = True


@router.get("", response_model=list[AuditLogResponse])
async def list_audit_logs(
    event_type: str | None = Query(None),
    resource_type: str | None = Query(None),
    actor_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[AuditLogResponse]:
    """Retrieve audit log entries with optional filtering and pagination."""
    stmt = select(AuditLog)
    if event_type:
        stmt = stmt.where(AuditLog.event_type == event_type)
    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)
    if actor_id:
        stmt = stmt.where(AuditLog.actor_id == actor_id)

    stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    logs = (await session.execute(stmt)).scalars().all()

    return [
        AuditLogResponse(
            id=log.id,
            event_type=log.event_type,
            actor_id=log.actor_id,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=json.loads(log.details_json) if log.details_json else None,
            ip_address=log.ip_address,
            request_id=log.request_id,
            created_at=log.created_at,
        )
        for log in logs
    ]
