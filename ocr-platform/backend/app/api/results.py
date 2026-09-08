"""Extraction results retrieval and export API endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models.extraction import ExtractedValue, ExtractionResult
from app.services.export.exporter import ResultExporter

router = APIRouter()


class BatchExportRequest(BaseModel):
    result_ids: list[str] = []
    format: str = "json"  # json | csv


async def _load_full_result(session: AsyncSession, result_id: str) -> ExtractionResult | None:
    """Helper to load ExtractionResult with values and evidence eagerly loaded."""
    stmt = (
        select(ExtractionResult)
        .where(ExtractionResult.id == result_id)
        .options(
            selectinload(ExtractionResult.values).selectinload(ExtractedValue.evidence)
        )
    )
    return (await session.execute(stmt)).scalar_one_or_none()


@router.get("/{result_id}")
async def get_extraction_result(
    result_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Retrieve full structured extraction result by ID."""
    result = await _load_full_result(session, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Extraction result not found")
    return ResultExporter.to_dict(result)


@router.get("/document/{document_id}")
async def get_latest_result_for_document(
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Retrieve the latest extraction result for a specific document."""
    stmt = (
        select(ExtractionResult)
        .where(ExtractionResult.document_id == document_id)
        .order_by(ExtractionResult.created_at.desc())
        .options(
            selectinload(ExtractionResult.values).selectinload(ExtractedValue.evidence)
        )
        .limit(1)
    )
    result = (await session.execute(stmt)).scalars().first()
    if not result:
        raise HTTPException(status_code=404, detail="No extraction result found for document")
    return ResultExporter.to_dict(result)


@router.get("/{result_id}/export")
async def export_single_result(
    result_id: str,
    format: str = Query("json", regex="^(json|csv)$"),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Export an extraction result as a downloadable JSON or CSV file."""
    result = await _load_full_result(session, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Extraction result not found")

    if format == "csv":
        content = ResultExporter.to_csv([result])
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="result_{result_id}.csv"'},
        )
    else:
        content = ResultExporter.to_json(result)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="result_{result_id}.json"'},
        )


@router.post("/batch-export")
async def batch_export_results(
    payload: BatchExportRequest,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Export multiple extraction results into a consolidated CSV or JSON file."""
    if not payload.result_ids:
        raise HTTPException(status_code=400, detail="result_ids cannot be empty")

    stmt = (
        select(ExtractionResult)
        .where(ExtractionResult.id.in_(payload.result_ids))
        .options(
            selectinload(ExtractionResult.values).selectinload(ExtractedValue.evidence)
        )
    )
    results = list((await session.execute(stmt)).scalars().all())
    if not results:
        raise HTTPException(status_code=404, detail="None of the specified results were found")

    fmt = payload.format.lower()
    if fmt == "csv":
        content = ResultExporter.to_csv(results)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="batch_export.csv"'},
        )
    else:
        content = ResultExporter.to_json(results)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="batch_export.json"'},
        )
