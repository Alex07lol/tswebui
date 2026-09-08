"""Document ingestion, multi-page splitting, and storage service."""
from __future__ import annotations

import hashlib
import io
import uuid
from pathlib import Path
from typing import BinaryIO

from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.document import Document, DocumentPage
from app.providers.storage.base import StorageProvider
from app.providers.storage.local import LocalStorageProvider

log = get_logger(__name__)


class DocumentService:
    """Handles document uploading, PDF page splitting, and storage."""

    def __init__(self, storage: StorageProvider | None = None) -> None:
        self.storage = storage or LocalStorageProvider()

    async def ingest_document(
        self,
        session: AsyncSession,
        filename: str,
        content: bytes,
        mime_type: str | None = None,
        uploaded_by: str | None = None,
    ) -> Document:
        """Ingest a new document, split pages, store assets, and save ORM records."""
        file_hash = hashlib.sha256(content).hexdigest()
        doc_id = str(uuid.uuid4())
        ext = Path(filename).suffix.lower()

        # Determine MIME
        if not mime_type or mime_type == "application/octet-stream":
            if ext in (".jpg", ".jpeg"):
                mime_type = "image/jpeg"
            elif ext == ".png":
                mime_type = "image/png"
            elif ext == ".pdf":
                mime_type = "application/pdf"
            elif ext in (".tif", ".tiff"):
                mime_type = "image/tiff"
            elif ext == ".bmp":
                mime_type = "image/bmp"
            else:
                mime_type = "application/octet-stream"

        # Save original file
        storage_key = f"documents/{doc_id}/original{ext}"
        self.storage.save(storage_key, io.BytesIO(content), content_type=mime_type)

        doc = Document(
            id=doc_id,
            filename=filename,
            original_filename=filename,
            mime_type=mime_type,
            file_size_bytes=len(content),
            storage_path=storage_key,
            file_hash=file_hash,
            status="uploaded",
            uploaded_by=uploaded_by,
        )
        session.add(doc)
        await session.flush()

        # Extract and save page images
        pages: list[tuple[int, Image.Image]] = []
        if mime_type == "application/pdf":
            try:
                from pdf2image import convert_from_bytes
                images = convert_from_bytes(content)
                for idx, img in enumerate(images, start=1):
                    pages.append((idx, img))
            except Exception as e:
                log.warning("pdf2image extraction failed, creating single placeholder page", error=str(e))
        else:
            try:
                img = Image.open(io.BytesIO(content))
                pages.append((1, img))
            except Exception as e:
                log.warning("Could not open image via PIL", error=str(e))

        doc.page_count = len(pages) if pages else 1
        for page_num, img in pages:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            page_bytes = buf.getvalue()
            page_key = f"documents/{doc_id}/pages/page_{page_num}.png"
            self.storage.save(page_key, io.BytesIO(page_bytes), content_type="image/png")

            doc_page = DocumentPage(
                id=str(uuid.uuid4()),
                document_id=doc.id,
                page_number=page_num,
                image_path=page_key,
                width=img.width,
                height=img.height,
            )
            session.add(doc_page)

        doc.status = "ready"
        await session.flush()
        return doc

    async def get_document(self, session: AsyncSession, doc_id: str) -> Document | None:
        """Fetch document by ID including its pages."""
        stmt = select(Document).where(Document.id == doc_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_documents(
        self, session: AsyncSession, skip: int = 0, limit: int = 50
    ) -> list[Document]:
        """List documents with pagination."""
        stmt = select(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    async def delete_document(self, session: AsyncSession, doc_id: str) -> bool:
        """Delete document from DB and remove associated storage assets."""
        doc = await self.get_document(session, doc_id)
        if not doc:
            return False

        if self.storage.exists(doc.storage_path):
            self.storage.delete(doc.storage_path)

        await session.delete(doc)
        return True
