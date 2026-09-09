"""Teach From Examples consumer API endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.services.ocr.service import OCRService
from app.services.teach.teach_service import TeachService

router = APIRouter()
ocr_service = OCRService()


class StartTeachSessionRequest(BaseModel):
    document_ids: list[str]


class SaveSetupFromTeachRequest(BaseModel):
    setup_name: str
    accepted_proposal_ids: list[str] | None = None


@router.post("/teach", status_code=status.HTTP_201_CREATED)
async def start_teach_session(
    payload: StartTeachSessionRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Start a teach session with a batch of documents."""
    if not payload.document_ids:
        raise HTTPException(status_code=400, detail="At least one document ID is required")

    teach_session = TeachService.start_session(payload.document_ids)

    # Process OCR for documents and analyze
    doc_map: dict[str, Any] = {}
    for doc_id in payload.document_ids:
        try:
            ocr_res = await ocr_service.process_document(session, doc_id)
            doc_map[doc_id] = ocr_res
        except Exception:
            continue

    TeachService.analyze(teach_session.session_id, doc_map)

    return {
        "session_id": teach_session.session_id,
        "status": teach_session.status,
        "document_count": len(payload.document_ids),
    }


@router.get("/teach/{session_id}")
async def get_teach_session(session_id: str) -> dict[str, Any]:
    """Check status of a teach session."""
    session = TeachService.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Teach session not found")

    return {
        "session_id": session.session_id,
        "status": session.status,
        "layout_count": len(session.layouts),
        "proposal_count": len(session.proposals),
    }


@router.get("/teach/{session_id}/layouts")
async def get_teach_layouts(session_id: str) -> dict[str, Any]:
    """Retrieve discovered document layouts."""
    session = TeachService.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Teach session not found")

    return {
        "layouts": [
            {
                "id": l.id,
                "label": l.label,
                "document_count": l.document_count,
                "sample_document_id": l.sample_document_id,
            }
            for l in session.layouts
        ]
    }


@router.get("/teach/{session_id}/proposals")
async def get_teach_proposals(session_id: str) -> dict[str, Any]:
    """Retrieve human-friendly proposed information fields."""
    session = TeachService.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Teach session not found")

    return {
        "proposals": [
            {
                "id": p.id,
                "suggested_name": p.suggested_name,
                "human_pattern": p.human_pattern,
                "example_found": p.example_found,
                "confidence_label": p.confidence_label,
                "confidence_score": p.confidence_score,
                "why": p.why,
                "action": p.action,
            }
            for p in session.proposals
        ]
    }


@router.post("/teach/{session_id}/save-setup", status_code=status.HTTP_201_CREATED)
async def save_setup_from_teach(
    session_id: str,
    payload: SaveSetupFromTeachRequest,
    db_session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Save accepted proposals as a new Setup."""
    try:
        setup = await TeachService.save_setup_from_teach(
            db_session=db_session,
            session_id=session_id,
            setup_name=payload.setup_name,
            accepted_proposal_ids=payload.accepted_proposal_ids,
        )
        return setup
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
