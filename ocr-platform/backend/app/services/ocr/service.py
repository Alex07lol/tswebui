"""OCR execution service with caching and persistence."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.document import Document
from app.models.ocr import OCRJob, OCRPage, OCRResult, OCRWord
from app.providers.ocr.base import OCROptions
from app.providers.ocr.registry import get_provider
from app.providers.storage.base import StorageProvider
from app.providers.storage.local import LocalStorageProvider

log = get_logger(__name__)


class OCRService:
    """Orchestrates OCR jobs, caching, and word/bbox persistence."""

    def __init__(self, storage: StorageProvider | None = None) -> None:
        self.storage = storage or LocalStorageProvider()

    def calculate_cache_key(
        self,
        file_hash: str,
        provider_name: str,
        provider_version: str,
        language: str,
        psm: int,
        oem: int,
    ) -> str:
        """Compute deterministic composite cache key."""
        raw = f"{file_hash}:{provider_name}:{provider_version}:{language}:{psm}:{oem}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def get_cached_result(
        self, session: AsyncSession, cache_key: str
    ) -> OCRResult | None:
        """Find existing OCRResult by cache key."""
        stmt = (
            select(OCRResult)
            .where(OCRResult.cache_key == cache_key)
            .order_by(OCRResult.created_at.desc())
            .limit(1)
            .options(selectinload(OCRResult.pages).selectinload(OCRPage.words))
        )
        res = await session.execute(stmt)
        return res.scalars().first()

    async def run_ocr_job(self, session: AsyncSession, job_id: str) -> OCRResult:
        """Execute an OCR job for a document and persist all results."""
        job_stmt = select(OCRJob).where(OCRJob.id == job_id)
        job = (await session.execute(job_stmt)).scalar_one_or_none()
        if not job:
            raise ValueError(f"OCRJob {job_id} not found")

        doc_stmt = (
            select(Document)
            .where(Document.id == job.document_id)
            .options(selectinload(Document.pages))
        )
        doc = (await session.execute(doc_stmt)).scalar_one_or_none()
        if not doc:
            job.status = "failed"
            job.error_message = f"Document {job.document_id} not found"
            await session.flush()
            raise ValueError(job.error_message)

        job.status = "running"
        job.started_at = datetime.now(timezone.utc).isoformat()
        await session.flush()

        provider = get_provider(job.provider)
        job.provider_version = provider.version

        options_dict = json.loads(job.options_json) if job.options_json else {}
        psm = int(options_dict.get("psm", 6))
        oem = int(options_dict.get("oem", 3))
        preprocessing = (
            json.loads(job.preprocessing_profile) if job.preprocessing_profile else None
        )

        cache_key = self.calculate_cache_key(
            file_hash=doc.file_hash or doc.id,
            provider_name=provider.name,
            provider_version=provider.version,
            language=job.language,
            psm=psm,
            oem=oem,
        )

        # Check cache
        cached = await self.get_cached_result(session, cache_key)
        if cached:
            log.info("OCR cache hit", document_id=doc.id, cache_key=cache_key)
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc).isoformat()

            # Ensure an OCRResult record exists tied directly to this document_id
            if cached.document_id != doc.id:
                doc_check_stmt = select(OCRResult).where(OCRResult.document_id == doc.id).limit(1)
                existing_for_doc = (await session.execute(doc_check_stmt)).scalars().first()
                if not existing_for_doc:
                    new_res = OCRResult(
                        id=str(uuid.uuid4()),
                        document_id=doc.id,
                        job_id=job.id,
                        provider=cached.provider,
                        provider_version=cached.provider_version,
                        language=cached.language,
                        full_text=cached.full_text,
                        cache_key=cache_key,
                    )
                    session.add(new_res)
                    await session.flush()
                    for p in cached.pages:
                        new_p = OCRPage(
                            id=str(uuid.uuid4()),
                            ocr_result_id=new_res.id,
                            page_number=p.page_number,
                            width=p.width,
                            height=p.height,
                            text=p.text,
                        )
                        session.add(new_p)
                        await session.flush()
                        for w in p.words:
                            new_w = OCRWord(
                                id=str(uuid.uuid4()),
                                page_id=new_p.id,
                                text=w.text,
                                confidence=w.confidence,
                                bbox_x=w.bbox_x,
                                bbox_y=w.bbox_y,
                                bbox_width=w.bbox_width,
                                bbox_height=w.bbox_height,
                                word_index=w.word_index,
                                line_number=w.line_number,
                                block_number=w.block_number,
                            )
                            session.add(new_w)
                    await session.flush()
                    cached = new_res

            await session.flush()
            return cached

        ocr_options = OCROptions(
            language=job.language,
            psm=psm,
            oem=oem,
            extra={"preprocessing": preprocessing},
        )

        all_page_texts: list[str] = []
        result_id = str(uuid.uuid4())
        ocr_result = OCRResult(
            id=result_id,
            document_id=doc.id,
            job_id=job.id,
            provider=provider.name,
            provider_version=provider.version,
            language=job.language,
            cache_key=cache_key,
        )
        session.add(ocr_result)
        await session.flush()

        pages_to_process = sorted(doc.pages, key=lambda p: p.page_number)
        if not pages_to_process:
            local_path = str(self.storage.get_local_path(doc.storage_path))
            res = provider.process(doc.id, local_path, ocr_options)
            all_page_texts.append(res.full_text)
        else:
            for page in pages_to_process:
                page_img_path = str(self.storage.get_local_path(page.image_path or doc.storage_path))
                provider_res = provider.process(doc.id, page_img_path, ocr_options)

                db_page = OCRPage(
                    id=str(uuid.uuid4()),
                    ocr_result_id=ocr_result.id,
                    page_number=page.page_number,
                    width=page.width,
                    height=page.height,
                    text=provider_res.full_text,
                )
                session.add(db_page)
                await session.flush()

                for w in (provider_res.pages[0].words if provider_res.pages else []):
                    db_word = OCRWord(
                        id=str(uuid.uuid4()),
                        page_id=db_page.id,
                        text=w.text,
                        confidence=w.confidence,
                        bbox_x=w.bounding_box.x,
                        bbox_y=w.bounding_box.y,
                        bbox_width=w.bounding_box.width,
                        bbox_height=w.bounding_box.height,
                        word_index=w.word_index,
                        line_number=w.line_number,
                        block_number=w.block_number,
                    )
                    session.add(db_word)

                all_page_texts.append(provider_res.full_text)

        ocr_result.full_text = "\n\n--- PAGE BREAK ---\n\n".join(all_page_texts)
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc).isoformat()
        await session.flush()

        log.info("OCR completed successfully", document_id=doc.id, pages=len(pages_to_process))
        return ocr_result

    async def get_ocr_result_for_document(
        self, session: AsyncSession, document_id: str
    ) -> OCRResult | None:
        """Get the latest OCR result for a document with pages and words loaded."""
        stmt = (
            select(OCRResult)
            .where(OCRResult.document_id == document_id)
            .order_by(OCRResult.created_at.desc())
            .limit(1)
            .options(selectinload(OCRResult.pages).selectinload(OCRPage.words))
        )
        res = await session.execute(stmt)
        return res.scalars().first()
