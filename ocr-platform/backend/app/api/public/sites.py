"""Public API endpoints for consumer document portals and secure file streaming."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models.document import Document, DocumentPage
from app.models.locator import SearchIndexMetadata
from app.models.website import DocumentVisibility, Website, WebsiteCollection, WebsiteVersion
from app.providers.search.database import DatabaseSearchProvider
from app.providers.storage.local import LocalStorageProvider

router = APIRouter()


async def _get_published_site(slug: str, session: AsyncSession) -> Website:
    """Fetch website by slug and verify published status."""
    stmt = (
        select(Website)
        .options(
            selectinload(Website.versions),
            selectinload(Website.collections),
        )
        .where(Website.slug == slug)
    )
    site = (await session.execute(stmt)).scalars().first()
    if not site:
        raise HTTPException(status_code=404, detail=f"Public portal '{slug}' not found.")
    if site.status != "published":
        raise HTTPException(status_code=403, detail="This document portal is currently offline or unpublished.")
    return site


@router.get("/sites/{slug}")
async def get_public_site_config(
    slug: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Retrieve public website configuration, theme, and search mappings."""
    site = await _get_published_site(slug, session)

    # Find active published version
    pub_ver = next((v for v in reversed(site.versions) if v.status == "published"), None)
    if not pub_ver:
        pub_ver = site.versions[-1] if site.versions else None

    theme = json.loads(pub_ver.theme_json) if pub_ver and pub_ver.theme_json else {}
    search_config = json.loads(pub_ver.search_config_json) if pub_ver and pub_ver.search_config_json else {}
    field_mappings = json.loads(pub_ver.field_mappings_json) if pub_ver and pub_ver.field_mappings_json else {}
    document_view = json.loads(pub_ver.document_view_json) if pub_ver and pub_ver.document_view_json else {}

    return {
        "name": site.name,
        "slug": site.slug,
        "description": site.description,
        "site_title": pub_ver.site_title if pub_ver else site.name,
        "tagline": pub_ver.tagline if pub_ver else "",
        "header_logo": pub_ver.header_logo if pub_ver else None,
        "theme": theme,
        "search_config": search_config,
        "field_mappings": field_mappings,
        "document_view": document_view,
        "collections": [
            {
                "name": c.name,
                "slug": c.slug,
                "description": c.description,
            }
            for c in site.collections
        ],
    }


@router.get("/sites/{slug}/search")
async def public_search(
    slug: str,
    q: str | None = Query(None, description="Search term for title, drawing number, or full text"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("relevance", regex="^(relevance|title|newest)$"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Execute ranked search over published documents."""
    site = await _get_published_site(slug, session)
    provider = DatabaseSearchProvider(session)

    res = await provider.search(
        website_id=site.id,
        query=q,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
    )

    return {
        "query": q,
        "total": res.total,
        "page": res.page,
        "page_size": res.page_size,
        "total_pages": res.total_pages,
        "hits": [
            {
                "document_id": h.document_id,
                "title": h.title,
                "drawing_number": h.drawing_number,
                "score": h.score,
                "rank_tier": h.rank_tier,
                "structured_fields": h.structured_fields,
                "snippet": h.snippet,
                "view_url": f"/sites/{slug}/documents/{h.document_id}",
                "file_url": f"/api/public/sites/{slug}/documents/{h.document_id}/file",
                "thumbnail_url": f"/api/public/sites/{slug}/documents/{h.document_id}/thumbnail",
            }
            for h in res.hits
        ],
    }


@router.get("/sites/{slug}/collections")
async def get_public_collections(
    slug: str,
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """List public collections available in this portal."""
    site = await _get_published_site(slug, session)
    return [
        {
            "name": c.name,
            "slug": c.slug,
            "description": c.description,
        }
        for c in site.collections
    ]


@router.get("/sites/{slug}/documents/{document_id}")
async def get_public_document_detail(
    slug: str,
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Retrieve metadata and view parameters for a single public document."""
    site = await _get_published_site(slug, session)

    # Check visibility gate
    vis_stmt = select(DocumentVisibility).where(
        DocumentVisibility.document_id == document_id,
        DocumentVisibility.website_id == site.id,
        DocumentVisibility.is_public == True,
    )
    vis = (await session.execute(vis_stmt)).scalars().first()
    if not vis:
        raise HTTPException(status_code=404, detail="Document not found or not published.")

    # Load indexed metadata
    idx_stmt = select(SearchIndexMetadata).where(
        SearchIndexMetadata.document_id == document_id,
        SearchIndexMetadata.website_id == site.id,
    )
    meta = (await session.execute(idx_stmt)).scalars().first()

    doc = await session.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document file record missing.")

    structured_fields = json.loads(meta.structured_fields_json) if meta and meta.structured_fields_json else {}

    return {
        "document_id": doc.id,
        "title": meta.title if meta else doc.original_filename,
        "drawing_number": meta.drawing_number if meta else None,
        "filename": doc.original_filename,
        "mime_type": doc.mime_type,
        "page_count": doc.page_count or 1,
        "structured_fields": structured_fields,
        "file_url": f"/api/public/sites/{slug}/documents/{doc.id}/file",
        "thumbnail_url": f"/api/public/sites/{slug}/documents/{doc.id}/thumbnail",
        "published_at": vis.published_at.isoformat() if vis.published_at else None,
    }


@router.get("/sites/{slug}/documents/{document_id}/file")
async def stream_public_document_file(
    slug: str,
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    """Stream PDF or image file securely with strict visibility verification."""
    site = await _get_published_site(slug, session)

    # Verify document is public for this site
    vis_stmt = select(DocumentVisibility).where(
        DocumentVisibility.document_id == document_id,
        DocumentVisibility.website_id == site.id,
        DocumentVisibility.is_public == True,
    )
    vis = (await session.execute(vis_stmt)).scalars().first()
    if not vis:
        raise HTTPException(status_code=404, detail="Document not found or private.")

    doc = await session.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document record not found.")

    storage = LocalStorageProvider()
    file_path = storage.get_local_path(doc.storage_path)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Stored document file not found.")

    return FileResponse(
        path=str(file_path),
        media_type=doc.mime_type or "application/pdf",
        filename=doc.original_filename,
    )


@router.get("/sites/{slug}/documents/{document_id}/thumbnail")
async def stream_public_thumbnail(
    slug: str,
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    """Stream thumbnail or first page image securely."""
    site = await _get_published_site(slug, session)

    # Verify visibility
    vis_stmt = select(DocumentVisibility).where(
        DocumentVisibility.document_id == document_id,
        DocumentVisibility.website_id == site.id,
        DocumentVisibility.is_public == True,
    )
    vis = (await session.execute(vis_stmt)).scalars().first()
    if not vis:
        raise HTTPException(status_code=404, detail="Document not found or private.")

    # Find page 1 image
    stmt = (
        select(DocumentPage)
        .where(DocumentPage.document_id == document_id, DocumentPage.page_number == 1)
    )
    page = (await session.execute(stmt)).scalars().first()

    storage = LocalStorageProvider()
    thumb_path = None
    if page and page.image_path:
        thumb_path = storage.get_local_path(page.image_path)

    if not thumb_path or not thumb_path.exists():
        # Fallback to original document if it's an image
        doc = await session.get(Document, document_id)
        if doc:
            thumb_path = storage.get_local_path(doc.storage_path)

    if not thumb_path or not thumb_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found.")

    return FileResponse(
        path=str(thumb_path),
        media_type="image/png",
    )
