"""API endpoints for active learning corrections."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.learning.corrections import (
    Correction,
    get_correction_engine,
)

router = APIRouter()


class SubmitCorrectionRequest(BaseModel):
    document_id: str
    field_name: str
    original_value: str | None = None
    corrected_value: str
    ocr_tokens: list[str] = []
    anchor_candidates: list[str] = []


class SubmitCorrectionResponse(BaseModel):
    field_name: str
    suggested_anchor_aliases: list[str]
    suggested_pattern: str | None
    confidence_delta: float


class InsightResponse(BaseModel):
    field_name: str
    suggested_anchor_aliases: list[str]
    suggested_pattern: str | None
    confidence_delta: float
    correction_count: int


@router.post("/corrections", response_model=SubmitCorrectionResponse)
async def submit_correction(body: SubmitCorrectionRequest) -> SubmitCorrectionResponse:
    """Submit a human correction for an extracted field."""
    engine = get_correction_engine()
    correction = Correction(
        document_id=body.document_id,
        field_name=body.field_name,
        original_value=body.original_value,
        corrected_value=body.corrected_value,
        ocr_tokens=body.ocr_tokens,
        anchor_candidates=body.anchor_candidates,
    )
    insight = engine.record(correction)
    return SubmitCorrectionResponse(
        field_name=insight.field_name,
        suggested_anchor_aliases=insight.suggested_anchor_aliases,
        suggested_pattern=insight.suggested_pattern,
        confidence_delta=insight.confidence_delta,
    )


@router.get("/corrections/{field_name}/insight", response_model=InsightResponse | None)
async def get_field_insight(field_name: str) -> InsightResponse | None:
    """Get accumulated learning insights for a field."""
    engine = get_correction_engine()
    insight = engine.get_insights(field_name)
    if insight is None:
        return None
    return InsightResponse(
        field_name=insight.field_name,
        suggested_anchor_aliases=insight.suggested_anchor_aliases,
        suggested_pattern=insight.suggested_pattern,
        confidence_delta=insight.confidence_delta,
        correction_count=engine.history_count(field_name),
    )


@router.get("/corrections/fields", response_model=list[str])
async def list_learned_fields() -> list[str]:
    """List all fields that have received corrections."""
    return get_correction_engine().all_field_names()
