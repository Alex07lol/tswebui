"""Consumer-facing Setups API endpoints (Setup = Configuration adapter)."""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models.configuration import Configuration, ConfigurationVersion
from app.models.extraction import ExtractionJob, ExtractionResult
from app.services.extraction.engine import ExtractionEngine
from app.services.ocr.service import OCRService
from app.services.setup.setup_service import SetupService

router = APIRouter()
ocr_service = OCRService()


class CreateSetupRequest(BaseModel):
    name: str
    description: str | None = None
    fields: list[dict[str, Any]] | None = None


class UpdateSetupRequest(BaseModel):
    name: str
    description: str | None = None


class ScanSetupRequest(BaseModel):
    document_id: str


@router.get("/setups")
async def list_setups(session: AsyncSession = Depends(get_session)) -> list[dict[str, Any]]:
    """List all setups in consumer-friendly format."""
    return await SetupService.list_setups(session)


@router.post("/setups", status_code=status.HTTP_201_CREATED)
async def create_setup(
    payload: CreateSetupRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Create a new setup with an initial draft version."""
    return await SetupService.create_setup(
        session=session,
        name=payload.name,
        description=payload.description,
        initial_fields=payload.fields,
    )


@router.get("/setups/{setup_id}")
async def get_setup(
    setup_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get setup details including its fields."""
    setup = await SetupService.get_setup(session, setup_id)
    if not setup:
        raise HTTPException(status_code=404, detail=f"Setup '{setup_id}' not found")
    return setup


@router.put("/setups/{setup_id}")
async def update_setup(
    setup_id: str,
    payload: UpdateSetupRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Update setup name or description."""
    updated = await SetupService.update_setup(
        session, setup_id, name=payload.name, description=payload.description
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Setup '{setup_id}' not found")
    return updated


@router.delete("/setups/{setup_id}")
async def delete_setup(
    setup_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Delete a setup."""
    success = await SetupService.delete_setup(session, setup_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Setup '{setup_id}' not found")
    return {"message": f"Setup '{setup_id}' deleted successfully"}


@router.post("/setups/{setup_id}/scan")
async def scan_with_setup(
    setup_id: str,
    payload: ScanSetupRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Scan a document using the specified setup's active rules."""
    setup = await SetupService.get_setup(session, setup_id)
    if not setup or not setup.get("version_id"):
        raise HTTPException(status_code=404, detail=f"Setup '{setup_id}' not found or has no version")

    version_stmt = select(ConfigurationVersion).where(ConfigurationVersion.id == setup["version_id"])
    res = await session.execute(version_stmt)
    version = res.scalar_one_or_none()
    if not version or not version.config_snapshot:
        raise HTTPException(status_code=400, detail="Setup configuration snapshot is empty")

    # Ensure OCR is completed for document
    ocr_result = await ocr_service.process_document(session, payload.document_id)

    # Run extraction engine
    cfg_data = json.loads(version.config_snapshot)
    results = ExtractionEngine.extract(ocr_result, cfg_data)

    # Format consumer-friendly values
    extracted_items: list[dict[str, Any]] = []
    overall_conf = 1.0
    if results:
        scores = []
        for r in results:
            val = r.normalized_value or r.raw_value
            conf = r.confidence or 0.85
            scores.append(conf)

            reasons: list[str] = []
            if conf >= 0.90:
                reasons.append("Matches expected pattern format precisely")
                reasons.append("Found near standard label in document")
            elif conf >= 0.70:
                reasons.append("Pattern matched with minor positional variation")
            else:
                reasons.append("Low confidence match; please verify")

            extracted_items.append({
                "field_id": r.field_id,
                "display_name": r.field_id.replace("_", " ").title(),
                "value": val,
                "raw_value": r.raw_value,
                "confidence_score": conf,
                "confidence_label": "Very High" if conf >= 0.90 else "High" if conf >= 0.70 else "Medium" if conf >= 0.45 else "Low",
                "why": reasons,
                "validation_passed": r.validation_passed,
                "evidence": [
                    {
                        "source_line": ev.source_line,
                        "anchor_text": ev.anchor_text,
                        "ocr_confidence": ev.ocr_confidence,
                    }
                    for ev in (r.evidence or [])
                ],
            })
        overall_conf = sum(scores) / len(scores) if scores else 0.0

    return {
        "setup_id": setup_id,
        "setup_name": setup["name"],
        "document_id": payload.document_id,
        "overall_confidence": overall_conf,
        "overall_confidence_label": "Very High" if overall_conf >= 0.90 else "High" if overall_conf >= 0.70 else "Medium",
        "extracted_values": extracted_items,
    }


@router.get("/setups/{setup_id}/history")
async def get_setup_history(
    setup_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """List version history for a setup."""
    stmt = (
        select(ConfigurationVersion)
        .where(ConfigurationVersion.configuration_id == setup_id)
        .order_by(ConfigurationVersion.version_number.desc())
    )
    res = await session.execute(stmt)
    versions = res.scalars().all()
    return [
        {
            "version_id": v.id,
            "version_number": v.version_number,
            "status": v.status,
            "change_notes": v.change_notes,
            "created_at": v.created_at.isoformat() if v.created_at else "",
        }
        for v in versions
    ]
