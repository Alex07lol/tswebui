"""Cross-document testing runner for extraction locators."""
from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document import Document
from app.models.locator import ExtractionLocator
from app.models.ocr import OCRResult, OCRPage
from app.services.locators.matcher import match_locator_against_page


async def test_locator_cross_documents(
    session: AsyncSession,
    locator: ExtractionLocator,
    document_ids: list[str] | None = None,
    limit: int = 10,
    confidence_threshold: float = 0.65,
) -> dict[str, Any]:
    """Test an ExtractionLocator against multiple OCR'd documents in the system.

    Args:
        session: Async database session.
        locator: Locator to evaluate.
        document_ids: Explicit list of document IDs to test, or None to test recent documents.
        limit: Max documents to test.
        confidence_threshold: Minimum confidence score to count as a match.

    Returns:
        Structured test summary with match rate and per-document outcomes.
    """
    stmt = (
        select(Document)
        .options(selectinload(Document.pages))
        .where(Document.status == "ready")
        .limit(limit)
    )
    if document_ids:
        stmt = stmt.where(Document.id.in_(document_ids))

    res = await session.execute(stmt)
    docs = res.scalars().all()

    if not docs:
        return {
            "total_tested": 0,
            "matched_count": 0,
            "match_rate": 0.0,
            "results": [],
        }

    results: list[dict[str, Any]] = []
    matched_count = 0

    for doc in docs:
        # Load OCR results for document
        ocr_stmt = (
            select(OCRResult)
            .options(selectinload(OCRResult.pages).selectinload(OCRPage.words))
            .where(OCRResult.document_id == doc.id)
            .order_by(OCRResult.created_at.desc())
            .limit(1)
        )
        ocr_res = (await session.execute(ocr_stmt)).scalars().first()

        doc_matched = False
        extracted_text = None
        cand_conf = 0.0
        cand_bbox = None
        page_num = 1

        if ocr_res and ocr_res.pages:
            # Check target page
            target_page = ocr_res.pages[0]
            if locator.page_mode == "specific" and locator.specific_page:
                for p in ocr_res.pages:
                    if p.page_number == locator.specific_page:
                        target_page = p
                        break

            page_words = [
                {
                    "text": w.text,
                    "confidence": w.confidence or 0.9,
                    "bbox_x": w.bbox_x or 0,
                    "bbox_y": w.bbox_y or 0,
                    "bbox_width": w.bbox_width or 20,
                    "bbox_height": w.bbox_height or 15,
                }
                for w in target_page.words
            ]

            pw = target_page.width or 800
            ph = target_page.height or 1050

            candidate = match_locator_against_page(
                locator=locator,
                page_words=page_words,
                page_width=pw,
                page_height=ph,
                page_number=target_page.page_number,
            )

            if candidate and candidate.confidence >= confidence_threshold:
                doc_matched = True
                extracted_text = candidate.text
                cand_conf = candidate.confidence
                cand_bbox = {
                    "x": candidate.bbox[0],
                    "y": candidate.bbox[1],
                    "width": candidate.bbox[2],
                    "height": candidate.bbox[3],
                }
                page_num = candidate.page_number

        if doc_matched:
            matched_count += 1

        results.append({
            "document_id": doc.id,
            "filename": doc.original_filename,
            "matched": doc_matched,
            "extracted_value": extracted_text,
            "confidence": cand_conf,
            "bbox": cand_bbox,
            "page_number": page_num,
        })

    match_rate = round(matched_count / len(docs), 3) if docs else 0.0

    return {
        "total_tested": len(docs),
        "matched_count": matched_count,
        "match_rate": match_rate,
        "results": results,
    }
