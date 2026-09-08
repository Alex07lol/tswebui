"""OCR job and result API endpoints."""
from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.ocr import OCRJob, OCRPage, OCRResult, OCRWord
from app.services.ocr.service import OCRService

router = APIRouter()
ocr_service = OCRService()


class CreateOCRJobRequest(BaseModel):
    document_id: str
    provider: str = "tesseract"
    language: str = "eng"
    psm: int = Field(6, ge=0, le=13)
    oem: int = Field(3, ge=0, le=3)
    preprocessing: list[Any] | None = None


class OCRJobResponse(BaseModel):
    id: str
    document_id: str
    status: str
    provider: str
    language: str
    error_message: str | None = None

    class Config:
        orm_mode = True


class OCRWordResponse(BaseModel):
    id: str
    text: str
    confidence: float | None
    bbox_x: int | None
    bbox_y: int | None
    bbox_width: int | None
    bbox_height: int | None
    word_index: int | None
    line_number: int | None

    class Config:
        orm_mode = True


class OCRPageResponse(BaseModel):
    page_number: int
    width: int | None
    height: int | None
    text: str | None
    words: list[OCRWordResponse] = []

    class Config:
        orm_mode = True


class OCRResultResponse(BaseModel):
    id: str
    document_id: str
    provider: str
    language: str
    full_text: str | None
    pages: list[OCRPageResponse] = []

    class Config:
        orm_mode = True


@router.post("/jobs", response_model=OCRJobResponse, status_code=status.HTTP_201_CREATED)
async def create_ocr_job(
    payload: CreateOCRJobRequest,
    session: AsyncSession = Depends(get_session),
) -> OCRJobResponse:
    """Create and execute an OCR job for a document."""
    job_id = str(uuid.uuid4())
    job = OCRJob(
        id=job_id,
        document_id=payload.document_id,
        status="pending",
        provider=payload.provider,
        language=payload.language,
        options_json=json.dumps({"psm": payload.psm, "oem": payload.oem}),
        preprocessing_profile=json.dumps(payload.preprocessing) if payload.preprocessing else None,
    )
    session.add(job)
    await session.flush()

    try:
        await ocr_service.run_ocr_job(session, job_id)
        await session.refresh(job)
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        await session.flush()
        raise HTTPException(status_code=500, detail=str(e))

    return OCRJobResponse(
        id=job.id,
        document_id=job.document_id,
        status=job.status,
        provider=job.provider,
        language=job.language,
        error_message=job.error_message,
    )


@router.get("/jobs/{job_id}", response_model=OCRJobResponse)
async def get_ocr_job(
    job_id: str,
    session: AsyncSession = Depends(get_session),
) -> OCRJobResponse:
    """Get status of an OCR job."""
    stmt = select(OCRJob).where(OCRJob.id == job_id)
    res = await session.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="OCR job not found")
    return OCRJobResponse(
        id=job.id,
        document_id=job.document_id,
        status=job.status,
        provider=job.provider,
        language=job.language,
        error_message=job.error_message,
    )


@router.get("/results/{document_id}", response_model=OCRResultResponse)
async def get_ocr_results(
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> OCRResultResponse:
    """Get full OCR results (pages, words, bounding boxes, confidence) for a document."""
    result = await ocr_service.get_ocr_result_for_document(session, document_id)
    if not result:
        raise HTTPException(status_code=404, detail="OCR result not found for document")

    pages_resp: list[OCRPageResponse] = []
    for p in result.pages:
        words_resp = [
            OCRWordResponse(
                id=w.id,
                text=w.text,
                confidence=w.confidence,
                bbox_x=w.bbox_x,
                bbox_y=w.bbox_y,
                bbox_width=w.bbox_width,
                bbox_height=w.bbox_height,
                word_index=w.word_index,
                line_number=w.line_number,
            )
            for w in p.words
        ]
        pages_resp.append(
            OCRPageResponse(
                page_number=p.page_number,
                width=p.width,
                height=p.height,
                text=p.text,
                words=words_resp,
            )
        )

    return OCRResultResponse(
        id=result.id,
        document_id=result.document_id,
        provider=result.provider,
        language=result.language,
        full_text=result.full_text,
        pages=pages_resp,
    )
