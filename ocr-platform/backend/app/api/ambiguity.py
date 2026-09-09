"""Ambiguity candidates inspection and resolution API endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.extraction.ambiguity import (
    get_ambiguity_candidates,
    resolve_candidate,
)

router = APIRouter()


class ResolveCandidateRequest(BaseModel):
    document_id: str
    chosen_value: str


@router.get("/setups/{setup_id}/fields/{field_id}/candidates")
async def get_candidates(
    setup_id: str,
    field_id: str,
    document_id: str,
) -> dict[str, Any]:
    """Retrieve all candidate matches for an ambiguous field."""
    state = get_ambiguity_candidates(setup_id, field_id, document_id)
    if not state:
        return {
            "field_id": field_id,
            "document_id": document_id,
            "ambiguous": False,
            "candidates": [],
        }

    return {
        "field_id": field_id,
        "document_id": document_id,
        "ambiguous": len(state.candidates) > 1,
        "resolved": state.resolved,
        "candidates": [
            {
                "value": c.value,
                "context_before": c.context_before,
                "context_after": c.context_after,
                "anchor_found": c.anchor_found,
                "confidence": c.confidence,
                "page": c.page,
                "bounding_box": c.bounding_box,
            }
            for c in state.candidates
        ],
    }


@router.post("/setups/{setup_id}/fields/{field_id}/resolve")
async def resolve_field_candidate(
    setup_id: str,
    field_id: str,
    payload: ResolveCandidateRequest,
) -> dict[str, Any]:
    """Resolve an ambiguous field by picking the user-selected value."""
    success, message, rule_patch = resolve_candidate(
        setup_id=setup_id,
        field_id=field_id,
        document_id=payload.document_id,
        chosen_value=payload.chosen_value,
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
        "rule_patch": rule_patch,
    }
