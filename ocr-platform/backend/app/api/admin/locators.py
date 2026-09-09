"""Admin API endpoints for Visual PDF Locators, Field Mapping, and Cross-Document Testing."""
from __future__ import annotations

import json
import re
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.admin.dependencies import require_admin_user
from app.core.database import get_session
from app.models.audit import AuditLog
from app.models.configuration import Configuration, ConfigurationVersion, ExtractionField, ExtractionRule
from app.models.locator import ExtractionLocator, LocatorExample
from app.models.user import User
from app.services.data.data_source_service import DataSourceService, infer_semantic_role
from app.services.locators import (
    analyze_pdf_selection,
    compile_locator_to_rule,
    create_locator_from_selection,
    learn_generalized_locator,
    test_locator_cross_documents,
)

router = APIRouter(dependencies=[Depends(require_admin_user)])


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
    field_id: str | None = None
    new_field_name: str | None = None
    new_field_type: str = "string"
    setup_id: str | None = None
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
async def analyze_selection(
    payload: AnalyzeSelectionRequest,
    admin_user: User = Depends(require_admin_user),
) -> dict[str, Any]:
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
    admin_user: User = Depends(require_admin_user),
) -> dict[str, Any]:
    """Save a visual extraction locator.
    
    Supports:
    1. Mapping to an existing field_id
    2. Creating a new field on-the-fly from the selection (new_field_name + setup_id)
    """
    field: ExtractionField | None = None

    if payload.field_id:
        field = await session.get(ExtractionField, payload.field_id)

    # If field doesn't exist yet or new_field_name is explicitly passed, create field on the fly
    if not field:
        field_name = (payload.new_field_name or payload.field_id or "Extracted Field").strip()
        field_key = re.sub(r"[^\w-]", "_", field_name.lower())

        # Resolve setup version
        version_id = None
        if payload.setup_id:
            stmt = (
                select(ConfigurationVersion)
                .where(ConfigurationVersion.configuration_id == payload.setup_id)
                .order_by(ConfigurationVersion.version_number.desc())
                .limit(1)
            )
            v = (await session.execute(stmt)).scalars().first()
            if v:
                version_id = v.id

        if not version_id:
            # Fallback to first available configuration version
            v_stmt = select(ConfigurationVersion).order_by(ConfigurationVersion.created_at.desc()).limit(1)
            v = (await session.execute(v_stmt)).scalars().first()
            if v:
                version_id = v.id

        if not version_id:
            # Create default configuration and version
            new_conf_id = str(uuid.uuid4())
            new_ver_id = str(uuid.uuid4())
            conf = Configuration(
                id=new_conf_id,
                name="Default Extraction Setup",
                slug=f"setup-{uuid.uuid4().hex[:6]}",
                description="Auto-generated setup for visual fields",
            )
            cver = ConfigurationVersion(
                id=new_ver_id,
                configuration_id=new_conf_id,
                version_number=1,
                status="draft",
            )
            session.add(conf)
            session.add(cver)
            await session.flush()
            version_id = new_ver_id

        field_id = str(uuid.uuid4())
        field = ExtractionField(
            id=field_id,
            version_id=version_id,
            field_id=field_key,
            display_name=field_name,
            output_variable=field_key,
            output_type=payload.new_field_type or "string",
            required=False,
        )
        session.add(field)
        await session.flush()

        # If linked to setup, sync to universal DataSource
        if payload.setup_id:
            ds_svc = DataSourceService(session)
            await ds_svc.sync_setup_to_data_source(payload.setup_id)

    p_bbox = tuple(payload.pixel_bbox) if payload.pixel_bbox and len(payload.pixel_bbox) == 6 else None

    locator = await create_locator_from_selection(
        session=session,
        field_id=field.id,
        selection_data=payload.selection_analysis,
        name=payload.name or f"Locator for {field.display_name}",
        template_label=payload.template_label or "Default Template",
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

    session.add(
        AuditLog(
            id=str(uuid.uuid4()),
            event_type="locator.created",
            resource_type="locator",
            resource_id=locator.id,
            details_json=json.dumps({"field_id": field.field_id, "name": locator.name}),
        )
    )
    await session.commit()

    return {
        "id": locator.id,
        "field_id": locator.field_id,
        "field_name": field.display_name,
        "name": locator.name,
        "template_label": locator.template_label,
        "compiled_rule_id": rule.id,
        "strategy": rule.strategy,
        "match_explanation": [
            f"Mapped to field '{field.display_name}' ({field.output_type})",
            f"Learned relative bbox at [{locator.rel_x:.3f}, {locator.rel_y:.3f}, {locator.rel_width:.3f}, {locator.rel_height:.3f}]",
            f"Captured {len(json.loads(locator.anchor_candidates_json or '[]'))} nearby text anchors",
        ],
    }


@router.get("/locators/{locator_id}")
async def get_locator(
    locator_id: str,
    session: AsyncSession = Depends(get_session),
    admin_user: User = Depends(require_admin_user),
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
    admin_user: User = Depends(require_admin_user),
) -> dict[str, Any]:
    """Run a cross-document test against documents and return match rate and explanations."""
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

    session.add(
        AuditLog(
            id=str(uuid.uuid4()),
            event_type="locator.tested",
            resource_type="locator",
            resource_id=loc.id,
            details_json=json.dumps({"match_rate": res["match_rate"], "total_tested": res["total_tested"]}),
        )
    )
    await session.commit()

    return res


@router.post("/locators/learn")
async def learn_locator(
    payload: LearnLocatorRequest,
    admin_user: User = Depends(require_admin_user),
) -> dict[str, Any]:
    """Generate a generalized locator configuration from multiple document annotations."""
    if not payload.examples:
        raise HTTPException(status_code=400, detail="Must provide at least one example.")
    return learn_generalized_locator(payload.examples)
