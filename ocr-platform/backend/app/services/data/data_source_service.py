"""Universal DataSource service: bridges OCR Setups to DataSources, syncs extractions, and manages generic records."""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.configuration import Configuration, ConfigurationVersion, ExtractionField
from app.models.data import (
    DataField,
    DataRecord,
    DataRelation,
    DataSchema,
    DataSource,
    WebsiteDataSource,
    WebsiteDocument,
)
from app.models.document import Document
from app.models.extraction import ExtractedValue, ExtractionResult


def infer_semantic_role(field_key: str, field_type: str = "string") -> str:
    """Heuristic role classifier for dynamic UI template generation."""
    key = field_key.lower().replace("-", "_")
    if any(k in key for k in ("title", "name", "headline", "item_name", "drawing_title", "product_name")):
        return "title"
    if any(k in key for k in ("number", "serial", "code", "dwg_no", "id", "sku", "identifier", "vin")):
        return "identifier"
    if any(k in key for k in ("date", "time", "year", "month", "expiry", "created")):
        return "date"
    if any(k in key for k in ("status", "state", "condition", "stage")):
        return "status"
    if any(k in key for k in ("category", "tag", "discipline", "project", "badge", "brand", "model", "type")):
        return "badge"
    if any(k in key for k in ("image", "photo", "thumbnail", "scan", "preview")):
        return "image"
    if any(k in key for k in ("pdf", "doc", "drawing", "attachment", "file")):
        return "document"
    if field_type in ("integer", "decimal", "currency", "percentage"):
        return "numeric"
    return "metadata"


class DataSourceService:
    """Service to bridge and manage Universal Data Sources, Schemas, Fields, and Records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def sync_setup_to_data_source(self, setup_id: str) -> DataSource | None:
        """Ensure an OCR Setup is mirrored into a DataSource and DataSchema."""
        stmt = (
            select(Configuration)
            .options(
                selectinload(Configuration.versions).selectinload(ConfigurationVersion.fields)
            )
            .where(Configuration.id == setup_id)
        )
        setup = (await self.session.execute(stmt)).scalars().first()
        if not setup:
            return None

        # 1. Find or create DataSource
        ds_stmt = select(DataSource).where(
            DataSource.setup_id == setup.id,
            DataSource.source_type == "ocr_records",
        )
        data_source = (await self.session.execute(ds_stmt)).scalars().first()

        if not data_source:
            slug = re.sub(r"[^\w\s-]", "", setup.name.lower()).strip()
            slug = re.sub(r"[-\s]+", "-", slug) or f"setup-{uuid.uuid4().hex[:6]}"
            # Ensure slug uniqueness
            existing_slug = (await self.session.execute(select(DataSource).where(DataSource.slug == slug))).scalars().first()
            if existing_slug:
                slug = f"{slug}-{uuid.uuid4().hex[:4]}"

            data_source = DataSource(
                id=str(uuid.uuid4()),
                name=setup.name,
                slug=slug,
                description=setup.description,
                source_type="ocr_records",
                setup_id=setup.id,
                status="active",
            )
            self.session.add(data_source)
            await self.session.flush()

        # 2. Find or create DataSchema
        schema_stmt = select(DataSchema).options(selectinload(DataSchema.fields)).where(
            DataSchema.data_source_id == data_source.id
        )
        schema = (await self.session.execute(schema_stmt)).scalars().first()

        if not schema:
            schema = DataSchema(
                id=str(uuid.uuid4()),
                data_source_id=data_source.id,
                name=f"{setup.name} Schema",
                version=1,
            )
            self.session.add(schema)
            await self.session.flush()

        # 3. Synchronize fields from active configuration version
        active_ver = setup.versions[-1] if setup.versions else None
        fields = active_ver.fields if active_ver else []

        existing_fields_map = {f.key: f for f in (schema.fields or [])}

        for idx, f in enumerate(fields):
            key = f.field_id or f.output_variable
            label = f.display_name or f.field_id
            field_type = f.output_type or "string"
            role = infer_semantic_role(key, field_type)
            is_req = getattr(f, "required", False)

            if key in existing_fields_map:
                df = existing_fields_map[key]
                df.label = label
                df.type = field_type
                df.required = is_req
                df.semantic_role = role
                df.display_order = idx
            else:
                df = DataField(
                    id=str(uuid.uuid4()),
                    schema_id=schema.id,
                    key=key,
                    label=label,
                    type=field_type,
                    required=is_req,
                    searchable=True,
                    sortable=True,
                    filterable=True,
                    displayable=True,
                    public_readable=True,
                    semantic_role=role,
                    display_order=idx,
                )
                self.session.add(df)

        await self.session.commit()
        return data_source

    async def sync_extraction_to_record(
        self, document_id: str, setup_id: str | None = None
    ) -> DataRecord | None:
        """Convert latest extracted values for a document into a normalized DataRecord."""
        # 1. Fetch document and extraction result
        doc = await self.session.get(Document, document_id)
        if not doc:
            return None

        ext_stmt = (
            select(ExtractionResult)
            .options(selectinload(ExtractionResult.values))
            .where(ExtractionResult.document_id == document_id)
            .order_by(ExtractionResult.created_at.desc())
            .limit(1)
        )
        ext_res = (await self.session.execute(ext_stmt)).scalars().first()
        if not ext_res or not ext_res.values:
            return None

        target_setup_id = setup_id or ext_res.configuration_id
        if not target_setup_id:
            return None

        # 2. Get or create data source for setup
        data_source = await self.sync_setup_to_data_source(target_setup_id)
        if not data_source:
            return None

        # 3. Build values map
        values: dict[str, Any] = {
            "_filename": doc.original_filename,
            "_document_id": doc.id,
        }
        for val in ext_res.values:
            field_key = val.field_id or val.output_variable
            values[field_key] = val.normalized_value or val.raw_value or ""

        # 4. Upsert DataRecord
        rec_stmt = select(DataRecord).where(
            DataRecord.data_source_id == data_source.id,
            DataRecord.source_document_id == document_id,
        )
        record = (await self.session.execute(rec_stmt)).scalars().first()

        if not record:
            record = DataRecord(
                id=str(uuid.uuid4()),
                data_source_id=data_source.id,
                source_document_id=document_id,
                values_json=json.dumps(values),
                status="active",
            )
            self.session.add(record)
        else:
            record.values_json = json.dumps(values)
            record.status = "active"

        await self.session.commit()
        return record

    async def create_custom_data_source(
        self,
        name: str,
        description: str | None = None,
        source_type: str = "manual",
        fields: list[dict[str, Any]] | None = None,
    ) -> DataSource:
        """Create a custom data source (e.g. warranties, certificates, products) with explicit schema."""
        slug = re.sub(r"[^\w\s-]", "", name.lower()).strip()
        slug = re.sub(r"[-\s]+", "-", slug) or f"source-{uuid.uuid4().hex[:6]}"
        existing_slug = (await self.session.execute(select(DataSource).where(DataSource.slug == slug))).scalars().first()
        if existing_slug:
            slug = f"{slug}-{uuid.uuid4().hex[:4]}"

        ds = DataSource(
            id=str(uuid.uuid4()),
            name=name,
            slug=slug,
            description=description,
            source_type=source_type,
            status="active",
        )
        self.session.add(ds)
        await self.session.flush()

        schema = DataSchema(
            id=str(uuid.uuid4()),
            data_source_id=ds.id,
            name=f"{name} Schema",
            version=1,
        )
        self.session.add(schema)
        await self.session.flush()

        for idx, f in enumerate(fields or []):
            field_key = f.get("key") or re.sub(r"[^\w-]", "_", f.get("label", "field").lower())
            field_type = f.get("type", "string")
            role = f.get("semantic_role") or infer_semantic_role(field_key, field_type)
            df = DataField(
                id=str(uuid.uuid4()),
                schema_id=schema.id,
                key=field_key,
                label=f.get("label", field_key.title()),
                type=field_type,
                required=f.get("required", False),
                searchable=f.get("searchable", True),
                sortable=f.get("sortable", True),
                filterable=f.get("filterable", True),
                displayable=f.get("displayable", True),
                public_readable=f.get("public_readable", True),
                semantic_role=role,
                display_order=idx,
            )
            self.session.add(df)

        await self.session.commit()
        return ds

    async def add_record_to_source(
        self, data_source_id: str, values: dict[str, Any], source_doc_id: str | None = None
    ) -> DataRecord:
        """Insert a single record into a data source."""
        rec = DataRecord(
            id=str(uuid.uuid4()),
            data_source_id=data_source_id,
            source_document_id=source_doc_id,
            values_json=json.dumps(values),
            status="active",
        )
        self.session.add(rec)
        await self.session.commit()
        return rec
