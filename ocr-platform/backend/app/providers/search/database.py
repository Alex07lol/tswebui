"""Database-backed search provider with ranked scoring and visibility filtering."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.locator import SearchIndexMetadata
from app.models.website import DocumentVisibility
from app.providers.search.base import SearchHit, SearchResult


class DatabaseSearchProvider:
    """Search provider implementation using database queries and python ranking."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def index_document(
        self,
        document_id: str,
        website_id: str,
        title: str | None,
        drawing_number: str | None,
        full_text: str | None,
        structured_fields: dict[str, Any],
    ) -> None:
        """Upsert document metadata into SearchIndexMetadata."""
        stmt = select(SearchIndexMetadata).where(
            SearchIndexMetadata.document_id == document_id,
            SearchIndexMetadata.website_id == website_id,
        )
        res = await self.session.execute(stmt)
        record = res.scalars().first()

        json_fields = json.dumps(structured_fields)

        if record:
            record.title = title
            record.drawing_number = drawing_number
            record.full_text = full_text
            record.structured_fields_json = json_fields
            record.indexed_at = datetime.now(timezone.utc)
        else:
            new_record = SearchIndexMetadata(
                id=str(uuid.uuid4()),
                document_id=document_id,
                website_id=website_id,
                title=title,
                drawing_number=drawing_number,
                full_text=full_text,
                structured_fields_json=json_fields,
                indexed_at=datetime.now(timezone.utc),
            )
            self.session.add(new_record)

        await self.session.commit()

    async def search(
        self,
        website_id: str,
        query: str | None = None,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "relevance",
        field_filters: dict[str, Any] | None = None,
    ) -> SearchResult:
        """Query index, calculate 5-tier ranked score, apply filters, and paginate."""
        filters = field_filters or filters
        # Only select documents that are public for this website
        stmt = (
            select(SearchIndexMetadata)
            .join(
                DocumentVisibility,
                (DocumentVisibility.document_id == SearchIndexMetadata.document_id)
                & (DocumentVisibility.website_id == website_id)
                & (DocumentVisibility.is_public == True),
            )
            .where(SearchIndexMetadata.website_id == website_id)
        )

        res = await self.session.execute(stmt)
        all_entries = res.scalars().all()

        clean_q = (query or "").strip().lower()
        scored_hits: list[SearchHit] = []

        for entry in all_entries:
            title = entry.title or ""
            drawing_no = entry.drawing_number or ""
            full_text = entry.full_text or ""
            structured = {}
            if entry.structured_fields_json:
                try:
                    structured = json.loads(entry.structured_fields_json)
                except Exception:
                    pass

            # Check explicit structured field filters
            if filters:
                mismatch = False
                for f_key, f_val in filters.items():
                    if f_val is not None:
                        actual_val = str(structured.get(f_key, "")).lower()
                        expected_val = str(f_val).lower()
                        if expected_val not in actual_val:
                            mismatch = True
                            break
                if mismatch:
                    continue

            # Calculate ranking score if query given
            score = 1.0
            tier = "all"
            snippet = None

            if clean_q:
                title_lower = title.lower()
                drawing_lower = drawing_no.lower()
                full_text_lower = full_text.lower()

                # Tier 1: Exact title match
                if clean_q == title_lower:
                    score = 1.00
                    tier = "exact_title"
                # Tier 2: Title prefix match
                elif title_lower.startswith(clean_q):
                    score = 0.85
                    tier = "prefix_title"
                # Tier 2b: Title contains word
                elif clean_q in title_lower:
                    score = 0.80
                    tier = "title_contain"
                # Tier 3: Drawing number match
                elif clean_q == drawing_lower:
                    score = 0.75
                    tier = "drawing_number_exact"
                elif clean_q in drawing_lower:
                    score = 0.70
                    tier = "drawing_number_partial"
                # Tier 4: Structured fields match
                elif any(clean_q in str(val).lower() for val in structured.values()):
                    score = 0.60
                    tier = "structured_field"
                # Tier 5: Full OCR text match
                elif clean_q in full_text_lower:
                    score = 0.40
                    tier = "ocr_text"
                    # Generate snippet
                    idx = full_text_lower.find(clean_q)
                    start = max(0, idx - 40)
                    end = min(len(full_text), idx + len(clean_q) + 40)
                    snippet = "..." + full_text[start:end].replace("\n", " ").strip() + "..."
                else:
                    # Query provided but document didn't match any tier
                    continue

            thumbnail_url = f"/api/public/sites/{website_id}/documents/{entry.document_id}/thumbnail"

            scored_hits.append(SearchHit(
                document_id=entry.document_id,
                title=title or f"Document {entry.document_id[:8]}",
                drawing_number=drawing_no or None,
                score=score,
                rank_tier=tier,
                structured_fields=structured,
                snippet=snippet,
                thumbnail_url=thumbnail_url,
            ))

        # Sort results
        if sort_by == "relevance":
            scored_hits.sort(key=lambda h: h.score, reverse=True)
        elif sort_by == "title":
            scored_hits.sort(key=lambda h: h.title.lower())
        elif sort_by == "newest":
            # Preserve natural indexed order (or newest)
            pass

        total = len(scored_hits)
        page_size = max(1, page_size)
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = max(1, min(page, total_pages))

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_hits = scored_hits[start_idx:end_idx]

        return SearchResult(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            hits=page_hits,
        )

    async def remove_document(self, document_id: str, website_id: str) -> None:
        """Delete search index record."""
        stmt = delete(SearchIndexMetadata).where(
            SearchIndexMetadata.document_id == document_id,
            SearchIndexMetadata.website_id == website_id,
        )
        await self.session.execute(stmt)
        await self.session.commit()
