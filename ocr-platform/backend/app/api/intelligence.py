"""AI-assisted rule and field suggestion endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.intelligence.suggestions import suggest_fields

router = APIRouter()


class SuggestRulesRequest(BaseModel):
    ocr_text: str
    top_k: int = 10


class FieldSuggestionOut(BaseModel):
    field_name: str
    confidence: float
    matched_alias: str
    pattern: str | None
    example: str
    strategy: str


class SuggestRulesResponse(BaseModel):
    suggestions: list[FieldSuggestionOut]
    total: int


@router.post("/intelligence/suggest-rules", response_model=SuggestRulesResponse)
async def suggest_rules(body: SuggestRulesRequest) -> SuggestRulesResponse:
    """Given raw OCR text, return AI-assisted field and rule suggestions."""
    results = suggest_fields(body.ocr_text, top_k=body.top_k)
    return SuggestRulesResponse(
        suggestions=[
            FieldSuggestionOut(
                field_name=s.field_name,
                confidence=s.confidence,
                matched_alias=s.matched_alias,
                pattern=s.pattern,
                example=s.example,
                strategy=s.strategy,
            )
            for s in results
        ],
        total=len(results),
    )
