"""Admin API endpoints for Visual PDF Locators, Field Mapping, and Cross-Document Testing."""
from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models.audit import AuditLog
from app.models.configuration import ExtractionField, ExtractionRule
from app.models.locator import ExtractionLocator, LocatorExample
from app.services.locators import (
    analyze_pdf_selection,
    compile_locator_to_rule,
    create_locator_from_selection,
    learn_generalized_locator,
    test_locator_cross_documents,
)

router = APIRouter()


class AnalyzeSelectionRequest(BaseModel):
    page_width: int
    page_height: int
    bbox_x: int
    bbox_y: int
    bbox_width: int
    bbox_height: int
    selected_text: str
    page_words: list[dict[str, Any]] = Field(default_factory=list)


class CreateLocatorRequest(BaseModel):
    field_id: str
    name: str | None = None
    template_label: str | None = None
    document_id: str | None = None
    page_number: int = 1
    selection_analysis: dict[str, Any]
    pixel_bbox: list[int] | None = None  # [bx, by, bw, bh, pw, ph]


class TestLocatorRequest(BaseModel):
    document_ids: list[str] | None = None
    limit: int = 10
    confidence_threshold: float = 0.65


class LearnLocatorRequest(BaseModel):
    examples: list[dict[str, Any]]


@router.post("/locators/analyze")
async def analyze_selection(payload: AnalyzeSelectionRequest) -> dict[str, Any]:
    """Analyze a visual drag/click selection on an OCR'd PDF/document page."""
    analysis = analyze_pdf_selection(
        page_width=payload.page_width,
        page_height=payload.page_height,
        bbox_x=payload.bbox_x,
        bbox_y=payload.bbox_y,
        bbox_width=payload.bbox_width,
        bbox_height=payload.bbox_height,
        selected_text=payload.selected_text,
        page_words=payload.page_words,
    )
    return analysis


@router.post("/locators")
async def create_locator(
    payload: CreateLocatorRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Save a visual extraction locator for an existing Setup field."""
    # Verify field exists
    field = await session.get(ExtractionField, payload.field_id)
    if not field:
        raise HTTPException(status_code=404, detail=f"Extraction field '{payload.field_id}' not found.")

    p_bbox = tuple(payload.pixel_bbox) if payload.pixel_bbox and len(payload.pixel_bbox) == 6 else None

    locator = await create_locator_from_selection(
        session=session,
        field_id=payload.field_id,
        selection_data=payload.selection_analysis,
        name=payload.name or f"Locator for {field.display_name}",
        template_label=payload.template_label,
        document_id=payload.document_id,
        page_number=payload.page_number,
        pixel_bbox=p_bbox,
    )

    # Automatically compile to an ExtractionRule and link to the field
    rule_dict = compile_locator_to_rule(locator, output_variable=field.output_variable)
    rule = ExtractionRule(
        id=str(uuid.uuid4()),
        field_id=field.id,
        rule_name=rule_dict["rule_name"],
        strategy=rule_dict["strategy"],
        anchor_config=rule_dict["anchor_config"],
        search_config=rule_dict["search_config"],
        pattern_config=rule_dict["pattern_config"],
        region_config=rule_dict["region_config"],
        priority=rule_dict["priority"],
        is_enabled=rule_dict["is_enabled"],
    )
    session.add(rule)

    session.add(AuditLog(
        id=str(uuid.uuid4()),
        event_type="locator.created",
        resource_type="locator",
        resource_id=locator.id,
        details_json=json.dumps({"field_id": field.field_id, "name": locator.name}),
    ))
    await session.commit()

    return {
        "id": locator.id,
        "field_id": locator.field_id,
        "name": locator.name,
        "template_label": locator.template_label,
        "compiled_rule_id": rule.id,
        "strategy": rule.strategy,
    }


@router.get("/locators/{locator_id}")
async def get_locator(
    locator_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Retrieve an ExtractionLocator and its ground-truth training examples."""
    stmt = (
        select(ExtractionLocator)
        .options(selectinload(ExtractionLocator.examples))
        .where(ExtractionLocator.id == locator_id)
    )
    loc = (await session.execute(stmt)).scalars().first()
    if not loc:
        raise HTTPException(status_code=404, detail="Locator not found.")

    anchors = json.loads(loc.anchor_candidates_json) if loc.anchor_candidates_json else []
    structure = json.loads(loc.structure_config_json) if loc.structure_config_json else {}

    return {
        "id": loc.id,
        "field_id": loc.field_id,
        "name": loc.name,
        "template_label": loc.template_label,
        "page_mode": loc.page_mode,
        "rel_x": loc.rel_x,
        "rel_y": loc.rel_y,
        "rel_width": loc.rel_width,
        "rel_height": loc.rel_height,
        "tolerance_x": loc.tolerance_x,
        "tolerance_y": loc.tolerance_y,
        "anchors": anchors,
        "structure": structure,
        "pattern_value": loc.pattern_value,
        "priority": loc.priority,
        "is_enabled": loc.is_enabled,
        "examples_count": len(loc.examples),
    }


@router.post("/locators/{locator_id}/test")
async def test_locator(
    locator_id: str,
    payload: TestLocatorRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Run a cross-document test against documents and return match rate."""
    loc = await session.get(ExtractionLocator, locator_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Locator not found.")

    res = await test_locator_cross_documents(
        session=session,
        locator=loc,
        document_ids=payload.document_ids,
        limit=payload.limit,
        confidence_threshold=payload.confidence_threshold,
    )

    session.add(AuditLog(
        id=str(uuid.uuid4()),
        event_type="locator.tested",
        resource_type="locator",
        resource_id=loc.id,
        details_json=json.dumps({"match_rate": res["match_rate"], "total_tested": res["total_tested"]}),
    ))
    await session.commit()

    return res


@router.post("/locators/learn")
async def learn_locator(payload: LearnLocatorRequest) -> dict[str, Any]:
    """Generate a generalized locator configuration from multiple document annotations."""
    if not payload.examples:
        raise HTTPException(status_code=400, detail="Must provide at least one example.")
    return learn_generalized_locator(payload.examples)
