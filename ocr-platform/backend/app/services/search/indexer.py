"""Search indexer service: extracts and compiles search documents from OCR and extracted values."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document import Document
from app.models.extraction import ExtractedValue, ExtractionResult
from app.models.ocr import OCRResult
from app.models.website import DocumentVisibility, Website
from app.providers.search.database import DatabaseSearchProvider


class SearchIndexer:
    """Synchronizes document OCR and extraction results into the SearchIndexMetadata table."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.provider = DatabaseSearchProvider(session)

    async def index_document_for_website(
        self,
        document_id: str,
        website_id: str,
        make_public: bool = True,
    ) -> None:
        """Extract metadata and full text, then index document for a website."""
        # 1. Fetch document
        doc = await self.session.get(Document, document_id)
        if not doc:
            return

        # 2. Fetch latest OCR result
        ocr_stmt = (
            select(OCRResult)
            .where(OCRResult.document_id == document_id)
            .order_by(OCRResult.created_at.desc())
            .limit(1)
        )
        ocr_res = (await self.session.execute(ocr_stmt)).scalars().first()
        full_text = ocr_res.full_text if ocr_res else ""

        # 3. Fetch latest extracted values
        ext_stmt = (
            select(ExtractionResult)
            .options(selectinload(ExtractionResult.values))
            .where(ExtractionResult.document_id == document_id)
            .order_by(ExtractionResult.created_at.desc())
            .limit(1)
        )
        ext_res = (await self.session.execute(ext_stmt)).scalars().first()

        structured_fields: dict[str, Any] = {}
        title = doc.original_filename
        drawing_number = None

        if ext_res and ext_res.values:
            for val in ext_res.values:
                field_key = val.field_id or val.output_variable
                extracted_str = val.normalized_value or val.raw_value or ""
                structured_fields[field_key] = extracted_str

                key_lower = field_key.lower()
                if key_lower in ("title", "document_title", "drawing_title", "name"):
                    if extracted_str:
                        title = extracted_str
                elif key_lower in ("drawing_number", "drawing_no", "dwg_no", "invoice_number", "doc_number"):
                    if extracted_str:
                        drawing_number = extracted_str

        # 4. Upsert DocumentVisibility
        vis_stmt = select(DocumentVisibility).where(
            DocumentVisibility.document_id == document_id,
            DocumentVisibility.website_id == website_id,
        )
        vis = (await self.session.execute(vis_stmt)).scalars().first()
        if not vis:
            vis = DocumentVisibility(
                document_id=document_id,
                website_id=website_id,
                is_public=make_public,
                published_at=datetime.now(timezone.utc) if make_public else None,
            )
            self.session.add(vis)
        elif make_public and not vis.is_public:
            vis.is_public = True
            vis.published_at = datetime.now(timezone.utc)

        await self.session.commit()

        # 5. Index into search provider
        await self.provider.index_document(
            document_id=document_id,
            website_id=website_id,
            title=title,
            drawing_number=drawing_number,
            full_text=full_text,
            structured_fields=structured_fields,
        )

    async def index_all_documents_for_website(self, website_id: str, make_public: bool = True) -> int:
        """Batch index all ready documents for a website."""
        stmt = select(Document.id).where(Document.status == "ready")
        doc_ids = (await self.session.execute(stmt)).scalars().all()

        indexed_count = 0
        for did in doc_ids:
            await self.index_document_for_website(did, website_id, make_public=make_public)
            indexed_count += 1

        return indexed_count
