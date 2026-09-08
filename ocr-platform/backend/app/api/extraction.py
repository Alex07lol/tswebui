"""Extraction jobs and persistent results API endpoints."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models.configuration import Configuration, ConfigurationVersion
from app.models.extraction import (
    ExtractionEvidence,
    ExtractionJob,
    ExtractionResult,
    ExtractedValue,
)
from app.services.extraction.engine import ExtractionEngine
from app.services.ocr.service import OCRService

router = APIRouter()
ocr_service = OCRService()


class RunExtractionRequest(BaseModel):
    document_id: str
    config_id: str
    version_number: int | None = None


@router.post("/jobs", status_code=status.HTTP_201_CREATED)
async def run_extraction_job(
    payload: RunExtractionRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Execute an extraction job for a document using a published configuration."""
    cfg_stmt = (
        select(Configuration)
        .where(Configuration.id == payload.config_id)
        .options(selectinload(Configuration.versions))
    )
    res = await session.execute(cfg_stmt)
    config = res.scalar_one_or_none()
    if not config or not config.versions:
        raise HTTPException(status_code=404, detail="Configuration not found")

    if payload.version_number:
        version = next(
            (v for v in config.versions if v.version_number == payload.version_number), None
        )
    else:
        # Prefer active version, fallback to latest
        active_versions = [v for v in config.versions if v.status == "active"]
        version = active_versions[0] if active_versions else max(config.versions, key=lambda v: v.version_number)

    if not version or not version.config_snapshot:
        raise HTTPException(status_code=400, detail="Configuration version has no valid rule snapshot")

    ocr_res = await ocr_service.get_ocr_result_for_document(session, payload.document_id)
    if not ocr_res:
        raise HTTPException(status_code=400, detail="OCR not performed on this document. Run OCR job first.")

    raw_cfg = json.loads(version.config_snapshot)
    extracted = ExtractionEngine.extract_document(ocr_res, raw_cfg)

    job_id = str(uuid.uuid4())
    job = ExtractionJob(
        id=job_id,
        document_id=payload.document_id,
        config_version_id=version.id,
        status="completed",
        started_at=datetime.now(timezone.utc).isoformat(),
        completed_at=datetime.now(timezone.utc).isoformat(),
    )
    session.add(job)

    result_id = str(uuid.uuid4())
    total_conf = sum(r.final_confidence for r in extracted.values())
    avg_conf = total_conf / len(extracted) if extracted else 1.0

    extraction_res = ExtractionResult(
        id=result_id,
        job_id=job_id,
        document_id=payload.document_id,
        config_version_id=version.id,
        overall_confidence=round(avg_conf, 4),
    )
    session.add(extraction_res)
    await session.flush()

    values_out: dict[str, Any] = {}
    for var_name, r in extracted.items():
        val_id = str(uuid.uuid4())
        val_record = ExtractedValue(
            id=val_id,
            result_id=result_id,
            field_id=r.field_id,
            output_variable=r.output_variable,
            raw_value=r.raw_value,
            normalized_value=r.normalized_value,
            final_confidence=r.final_confidence,
            validation_passed=r.validation_passed,
            validation_message=r.validation_message,
        )
        session.add(val_record)

        ev = r.evidence
        bbox = ev.get("bounding_box") or {}
        evidence_record = ExtractionEvidence(
            id=str(uuid.uuid4()),
            extracted_value_id=val_id,
            anchor_text=ev.get("anchor_text"),
            source_line=ev.get("source_line"),
            ocr_confidence=ev.get("ocr_confidence"),
            bbox_x=bbox.get("x"),
            bbox_y=bbox.get("y"),
            bbox_width=bbox.get("width"),
            bbox_height=bbox.get("height"),
            page_number=ev.get("page_number", 1),
        )
        session.add(evidence_record)

        values_out[var_name] = {
            "value": r.normalized_value or r.raw_value,
            "raw": r.raw_value,
            "confidence": r.final_confidence,
            "validation_passed": r.validation_passed,
            "evidence": ev,
        }

    await session.flush()

    return {
        "job_id": job_id,
        "result_id": result_id,
        "document_id": payload.document_id,
        "config_id": config.id,
        "version_number": version.version_number,
        "overall_confidence": round(avg_conf, 4),
        "fields": values_out,
    }


@router.get("/results/{result_id}")
async def get_extraction_result(
    result_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get persistent extraction result by result ID with all values and evidence."""
    stmt = (
        select(ExtractionResult)
        .where(ExtractionResult.id == result_id)
        .options(selectinload(ExtractionResult.values).selectinload(ExtractedValue.evidence))
    )
    res = await session.execute(stmt)
    result = res.scalar_one_or_none()
    if not result:
        raise HTTPException(status_code=404, detail="Extraction result not found")

    fields_dict: dict[str, Any] = {}
    for v in result.values:
        ev = v.evidence[0] if v.evidence else None
        fields_dict[v.output_variable] = {
            "field_id": v.field_id,
            "raw_value": v.raw_value,
            "normalized_value": v.normalized_value,
            "final_confidence": v.final_confidence,
            "validation_passed": v.validation_passed,
            "evidence": {
                "anchor_text": ev.anchor_text if ev else None,
                "source_line": ev.source_line if ev else None,
                "ocr_confidence": ev.ocr_confidence if ev else None,
                "bbox": (
                    {"x": ev.bbox_x, "y": ev.bbox_y, "width": ev.bbox_width, "height": ev.bbox_height}
                    if ev
                    else None
                ),
            },
        }

    return {
        "id": result.id,
        "document_id": result.document_id,
        "config_version_id": result.config_version_id,
        "overall_confidence": result.overall_confidence,
        "fields": fields_dict,
    }
