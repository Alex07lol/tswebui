"""Admin API endpoints for managing Universal DataSources, Schemas, Fields, and Records."""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.admin.dependencies import require_admin_user
from app.core.database import get_session
from app.models.data import DataField, DataRecord, DataSchema, DataSource
from app.models.user import User
from app.services.data.data_source_service import DataSourceService

router = APIRouter()


class CreateFieldInput(BaseModel):
    key: str
    label: str
    type: str = "string"
    required: bool = False
    searchable: bool = True
    sortable: bool = True
    filterable: bool = True
    displayable: bool = True
    public_readable: bool = True
    semantic_role: str | None = None


class CreateDataSourceRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    source_type: str = "manual"  # manual | ocr_records | imported | computed
    fields: list[CreateFieldInput] = []


class CreateRecordRequest(BaseModel):
    values: dict[str, Any]
    source_document_id: str | None = None


@router.get("/data-sources")
async def list_data_sources(
    session: AsyncSession = Depends(get_session),
    admin_user: User = Depends(require_admin_user),
) -> list[dict[str, Any]]:
    """List all registered DataSources with schemas and field summaries."""
    stmt = (
        select(DataSource)
        .options(
            selectinload(DataSource.schemas).selectinload(DataSchema.fields),
            selectinload(DataSource.records),
        )
        .order_by(desc(DataSource.created_at))
    )
    sources = (await session.execute(stmt)).scalars().all()

    out = []
    for s in sources:
        active_schema = s.schemas[0] if s.schemas else None
        fields_summary = []
        if active_schema:
            fields_summary = [
                {
                    "id": f.id,
                    "key": f.key,
                    "label": f.label,
                    "type": f.type,
                    "semantic_role": f.semantic_role,
                    "public_readable": f.public_readable,
                }
                for f in active_schema.fields
            ]

        out.append({
            "id": s.id,
            "name": s.name,
            "slug": s.slug,
            "description": s.description,
            "source_type": s.source_type,
            "setup_id": s.setup_id,
            "status": s.status,
            "record_count": len(s.records),
            "fields": fields_summary,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })
    return out


@router.post("/data-sources")
async def create_data_source(
    payload: CreateDataSourceRequest,
    session: AsyncSession = Depends(get_session),
    admin_user: User = Depends(require_admin_user),
) -> dict[str, Any]:
    """Create a new custom DataSource with schema fields."""
    svc = DataSourceService(session)
    fields_data = [
        (f.model_dump() if hasattr(f, "model_dump") else f.dict())
        for f in payload.fields
    ]
    ds = await svc.create_custom_data_source(
        name=payload.name,
        description=payload.description,
        source_type=payload.source_type,
        fields=fields_data,
    )
    return {
        "id": ds.id,
        "name": ds.name,
        "slug": ds.slug,
        "source_type": ds.source_type,
        "status": ds.status,
    }


@router.post("/data-sources/sync-setup/{setup_id}")
async def sync_setup_to_data_source(
    setup_id: str,
    session: AsyncSession = Depends(get_session),
    admin_user: User = Depends(require_admin_user),
) -> dict[str, Any]:
    """Sync an OCR Setup into a DataSource and DataSchema."""
    svc = DataSourceService(session)
    ds = await svc.sync_setup_to_data_source(setup_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Setup '{setup_id}' not found.")
    return {
        "status": "ok",
        "data_source_id": ds.id,
        "slug": ds.slug,
        "name": ds.name,
    }


@router.get("/data-sources/{source_id}")
async def get_data_source(
    source_id: str,
    session: AsyncSession = Depends(get_session),
    admin_user: User = Depends(require_admin_user),
) -> dict[str, Any]:
    """Retrieve full DataSource schema and recent sample records."""
    stmt = (
        select(DataSource)
        .options(
            selectinload(DataSource.schemas).selectinload(DataSchema.fields),
            selectinload(DataSource.records),
        )
        .where(DataSource.id == source_id)
    )
    ds = (await session.execute(stmt)).scalars().first()
    if not ds:
        raise HTTPException(status_code=404, detail=f"DataSource '{source_id}' not found.")

    active_schema = ds.schemas[0] if ds.schemas else None
    fields = []
    if active_schema:
        fields = [
            {
                "id": f.id,
                "key": f.key,
                "label": f.label,
                "type": f.type,
                "required": f.required,
                "searchable": f.searchable,
                "sortable": f.sortable,
                "filterable": f.filterable,
                "displayable": f.displayable,
                "public_readable": f.public_readable,
                "semantic_role": f.semantic_role,
            }
            for f in active_schema.fields
        ]

    sample_records = []
    for r in ds.records[:20]:
        vals = json.loads(r.values_json) if r.values_json else {}
        sample_records.append({
            "id": r.id,
            "values": vals,
            "status": r.status,
            "source_document_id": r.source_document_id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    return {
        "id": ds.id,
        "name": ds.name,
        "slug": ds.slug,
        "description": ds.description,
        "source_type": ds.source_type,
        "setup_id": ds.setup_id,
        "fields": fields,
        "records": sample_records,
        "total_records": len(ds.records),
    }


@router.post("/data-sources/{source_id}/records")
async def add_record_to_source(
    source_id: str,
    payload: CreateRecordRequest,
    session: AsyncSession = Depends(get_session),
    admin_user: User = Depends(require_admin_user),
) -> dict[str, Any]:
    """Insert a new structured record into a DataSource."""
    svc = DataSourceService(session)
    rec = await svc.add_record_to_source(
        data_source_id=source_id,
        values=payload.values,
        source_doc_id=payload.source_document_id,
    )
    return {"id": rec.id, "status": rec.status}
