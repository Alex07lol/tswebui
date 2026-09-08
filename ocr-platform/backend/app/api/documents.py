"""Document management API endpoints."""
from __future__ import annotations

import io
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.services.document_service import DocumentService

router = APIRouter()
doc_service = DocumentService()


class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    file_hash: str | None
    page_count: int | None
    status: str

    class Config:
        orm_mode = True


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> DocumentResponse:
    """Upload a document (PDF, PNG, JPG, TIFF, BMP)."""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file provided")

    doc = await doc_service.ingest_document(
        session=session,
        filename=file.filename or "uploaded_file",
        content=content,
        mime_type=file.content_type,
    )
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        original_filename=doc.original_filename,
        mime_type=doc.mime_type,
        file_size_bytes=doc.file_size_bytes,
        file_hash=doc.file_hash,
        page_count=doc.page_count,
        status=doc.status,
    )


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
) -> list[DocumentResponse]:
    """List uploaded documents."""
    docs = await doc_service.list_documents(session, skip=skip, limit=limit)
    return [
        DocumentResponse(
            id=d.id,
            filename=d.filename,
            original_filename=d.original_filename,
            mime_type=d.mime_type,
            file_size_bytes=d.file_size_bytes,
            file_hash=d.file_hash,
            page_count=d.page_count,
            status=d.status,
        )
        for d in docs
    ]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> DocumentResponse:
    """Get document metadata by ID."""
    doc = await doc_service.get_document(session, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        original_filename=doc.original_filename,
        mime_type=doc.mime_type,
        file_size_bytes=doc.file_size_bytes,
        file_hash=doc.file_hash,
        page_count=doc.page_count,
        status=doc.status,
    )


@router.get("/{document_id}/file")
async def get_document_file(
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Download original document file."""
    doc = await doc_service.get_document(session, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc_service.storage.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document file not found in storage")
    data = doc_service.storage.load(doc.storage_path)
    return Response(
        content=data,
        media_type=doc.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{doc.original_filename}"'},
    )


@router.get("/{document_id}/pages/{page_number}/image")
async def get_document_page_image(
    document_id: str,
    page_number: int,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Get rendered PNG image for a specific page."""
    doc = await doc_service.get_document(session, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    page_key = f"documents/{document_id}/pages/page_{page_number}.png"
    if not doc_service.storage.exists(page_key):
        # Fallback to original if single page and it exists
        if doc_service.storage.exists(doc.storage_path) and doc.mime_type.startswith("image/"):
            data = doc_service.storage.load(doc.storage_path)
            return Response(content=data, media_type=doc.mime_type)
        raise HTTPException(status_code=404, detail="Page image not found")
    data = doc_service.storage.load(page_key)
    return Response(content=data, media_type="image/png")


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a document and its stored files."""
    deleted = await doc_service.delete_document(session, document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")

