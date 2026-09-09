"""Training pipeline API endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.ocr.training import evaluate_ocr

router = APIRouter()


class EvaluateOCRRequest(BaseModel):
    predicted_text: str
    ground_truth_text: str


class EvaluateOCRResponse(BaseModel):
    cer: float
    wer: float
    char_count: int
    word_count: int
    edits: int
    cer_percent: float
    wer_percent: float


@router.post("/training/evaluate", response_model=EvaluateOCRResponse)
async def evaluate_ocr_quality(body: EvaluateOCRRequest) -> EvaluateOCRResponse:
    """Compute CER and WER for OCR output vs ground truth."""
    metrics = evaluate_ocr(body.predicted_text, body.ground_truth_text)
    return EvaluateOCRResponse(
        cer=metrics.cer,
        wer=metrics.wer,
        char_count=metrics.char_count,
        word_count=metrics.word_count,
        edits=metrics.edits,
        cer_percent=round(metrics.cer * 100, 2),
        wer_percent=round(metrics.wer * 100, 2),
    )
