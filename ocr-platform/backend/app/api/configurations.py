"""Configuration CRUD, versioning, and test extraction API endpoints."""
from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models.configuration import (
    Configuration,
    ConfigurationVersion,
)
from app.schemas.configuration import ConfigurationSchema
from app.services.extraction.engine import ExtractionEngine
from app.services.ocr.service import OCRService

router = APIRouter()
ocr_service = OCRService()


class CreateConfigRequest(BaseModel):
    name: str
    slug: str
    description: str | None = None
    config: ConfigurationSchema | dict[str, Any] | None = None


class TestConfigRequest(BaseModel):
    document_id: str
    config: ConfigurationSchema | dict[str, Any]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_configuration(
    payload: CreateConfigRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Create a new extraction configuration or add a draft version if slug exists."""
    existing_stmt = (
        select(Configuration)
        .where(Configuration.slug == payload.slug)
        .options(selectinload(Configuration.versions))
    )
    res = await session.execute(existing_stmt)
    existing = res.scalar_one_or_none()

    raw_config = (
        payload.config.dict()
        if hasattr(payload.config, "dict")
        else (payload.config or {"schema_version": 1, "id": payload.slug, "name": payload.name, "fields": []})
    )

    if existing:
        next_ver_num = (
            max(v.version_number for v in existing.versions) + 1 if existing.versions else 1
        )
        version = ConfigurationVersion(
            id=str(uuid.uuid4()),
            configuration_id=existing.id,
            version_number=next_ver_num,
            status="draft",
            config_snapshot=json.dumps(raw_config),
        )
        session.add(version)
        await session.flush()
        return {
            "id": existing.id,
            "name": existing.name,
            "slug": existing.slug,
            "current_version": version.version_number,
            "status": version.status,
        }

    config_id = str(uuid.uuid4())
    config = Configuration(
        id=config_id,
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
    )
    session.add(config)

    version_id = str(uuid.uuid4())
    version = ConfigurationVersion(
        id=version_id,
        configuration_id=config_id,
        version_number=1,
        status="draft",
        config_snapshot=json.dumps(raw_config),
    )
    session.add(version)
    await session.flush()

    return {
        "id": config.id,
        "name": config.name,
        "slug": config.slug,
        "current_version": version.version_number,
        "status": version.status,
    }


@router.get("")
async def list_configurations(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """List all extraction configurations."""
    stmt = (
        select(Configuration)
        .options(selectinload(Configuration.versions))
        .order_by(Configuration.created_at.desc())
    )
    res = await session.execute(stmt)
    configs = res.scalars().all()

    out: list[dict[str, Any]] = []
    for c in configs:
        latest_ver = (
            max(c.versions, key=lambda v: v.version_number) if c.versions else None
        )
        out.append(
            {
                "id": c.id,
                "name": c.name,
                "slug": c.slug,
                "description": c.description,
                "version": latest_ver.version_number if latest_ver else 1,
                "status": latest_ver.status if latest_ver else "draft",
            }
        )
    return out


@router.get("/{config_id}")
async def get_configuration(
    config_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get full configuration with versions and latest config snapshot."""
    stmt = (
        select(Configuration)
        .where(Configuration.id == config_id)
        .options(selectinload(Configuration.versions))
    )
    res = await session.execute(stmt)
    config = res.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    latest_ver = (
        max(config.versions, key=lambda v: v.version_number) if config.versions else None
    )
    snapshot = json.loads(latest_ver.config_snapshot) if (latest_ver and latest_ver.config_snapshot) else {}

    return {
        "id": config.id,
        "name": config.name,
        "slug": config.slug,
        "description": config.description,
        "latest_version": latest_ver.version_number if latest_ver else 1,
        "status": latest_ver.status if latest_ver else "draft",
        "config": snapshot,
    }


@router.post("/{config_id}/publish")
async def publish_configuration(
    config_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Publish the latest draft configuration version to active status."""
    stmt = (
        select(Configuration)
        .where(Configuration.id == config_id)
        .options(selectinload(Configuration.versions))
    )
    res = await session.execute(stmt)
    config = res.scalar_one_or_none()
    if not config or not config.versions:
        raise HTTPException(status_code=404, detail="Configuration not found")

    for v in config.versions:
        if v.status == "active":
            v.status = "deprecated"

    latest_ver = max(config.versions, key=lambda v: v.version_number)
    latest_ver.status = "active"
    await session.flush()

    return {
        "id": config.id,
        "version_number": latest_ver.version_number,
        "status": latest_ver.status,
    }


@router.post("/test/live")
async def test_extraction_live(
    payload: TestConfigRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Test extraction rules on a document's OCR result without saving."""
    ocr_res = await ocr_service.get_ocr_result_for_document(session, payload.document_id)
    if not ocr_res:
        raise HTTPException(status_code=404, detail="OCR results not found for document. Run OCR first.")

    raw_cfg = (
        payload.config.dict()
        if hasattr(payload.config, "dict")
        else payload.config
    )
    results = ExtractionEngine.extract_document(ocr_res, raw_cfg)

    serialized: dict[str, Any] = {}
    for var_name, r in results.items():
        serialized[var_name] = {
            "field_id": r.field_id,
            "raw_value": r.raw_value,
            "normalized_value": r.normalized_value,
            "final_confidence": r.final_confidence,
            "confidence_breakdown": r.confidence_breakdown,
            "validation_passed": r.validation_passed,
            "validation_message": r.validation_message,
            "evidence": r.evidence,
        }

    return {"document_id": payload.document_id, "extracted_fields": serialized}
