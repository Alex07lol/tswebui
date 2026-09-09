"""Public API endpoints for consumer document portals, search, and secure file streaming."""
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
from app.models.website import Website, WebsiteCollection, WebsitePage, WebsiteVersion
from app.providers.storage.local import LocalStorageProvider
from app.services.search.public_site_service import PublicSiteService

router = APIRouter()


@router.get("/sites")
async def list_public_sites(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """List all currently published portals for public discovery."""
    svc = PublicSiteService(session)
    return await svc.list_published_websites()


@router.get("/sites/{slug}")
async def get_public_site_config(
    slug: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Retrieve public website configuration, theme, pages, and components from published snapshot."""
    svc = PublicSiteService(session)
    try:
        site, pub_ver = await svc.get_published_website(slug)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Public portal '{slug}' not found.")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    theme = json.loads(pub_ver.theme_json) if pub_ver.theme_json else {}
    search_config = json.loads(pub_ver.search_config_json) if pub_ver.search_config_json else {}
    field_mappings = json.loads(pub_ver.field_mappings_json) if pub_ver.field_mappings_json else {}
    document_view = json.loads(pub_ver.document_view_json) if pub_ver.document_view_json else {}
    bindings = json.loads(pub_ver.bindings_json) if pub_ver.bindings_json else {}
    actions = json.loads(pub_ver.actions_json) if pub_ver.actions_json else {}
    conditions = json.loads(pub_ver.conditions_json) if pub_ver.conditions_json else {}
    computed_fields = json.loads(pub_ver.computed_fields_json) if pub_ver.computed_fields_json else {}

    pages = []
    if pub_ver.pages:
        for p in pub_ver.pages:
            pages.append({
                "id": p.id,
                "page_type": p.page_type,
                "title": p.title,
                "slug": p.slug,
                "layout_config": json.loads(p.layout_config_json) if p.layout_config_json else {},
                "components": json.loads(p.components_json) if p.components_json else [],
                "display_order": p.display_order,
            })

    return {
        "name": site.name,
        "slug": site.slug,
        "description": site.description,
        "site_title": pub_ver.site_title or site.name,
        "tagline": pub_ver.tagline or "",
        "header_logo": pub_ver.header_logo,
        "version_number": pub_ver.version_number,
        "theme": theme,
        "search_config": search_config,
        "field_mappings": field_mappings,
        "document_view": document_view,
        "bindings": bindings,
        "actions": actions,
        "conditions": conditions,
        "computed_fields": computed_fields,
        "pages": pages,
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
    q: str | None = Query(None, description="Search term for title, identifier, or full text"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("relevance", regex="^(relevance|title|newest)$"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Execute ranked search over published documents."""
    svc = PublicSiteService(session)
    try:
        site, _ = await svc.get_published_website(slug)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Public portal '{slug}' not found.")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    res = await svc.execute_search(
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


@router.get("/sites/{slug}/collections/{coll_slug}")
async def get_collection_detail_and_documents(
    slug: str,
    coll_slug: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Query documents for a specific curated collection."""
    svc = PublicSiteService(session)
    try:
        site, _ = await svc.get_published_website(slug)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Public portal '{slug}' not found.")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    coll = next((c for c in site.collections if c.slug == coll_slug), None)
    if not coll:
        raise HTTPException(status_code=404, detail=f"Collection '{coll_slug}' not found.")

    res = await svc.get_collection_documents(
        website_id=site.id,
        collection=coll,
        page=page,
        page_size=page_size,
    )

    return {
        "collection": {
            "name": coll.name,
            "slug": coll.slug,
            "description": coll.description,
        },
        "total": res.total,
        "page": res.page,
        "page_size": res.page_size,
        "total_pages": res.total_pages,
        "hits": [
            {
                "document_id": h.document_id,
                "title": h.title,
                "drawing_number": h.drawing_number,
                "structured_fields": h.structured_fields,
                "file_url": f"/api/public/sites/{slug}/documents/{h.document_id}/file",
                "thumbnail_url": f"/api/public/sites/{slug}/documents/{h.document_id}/thumbnail",
            }
            for h in res.hits
        ],
    }


@router.get("/sites/{slug}/documents/{document_id}")
async def get_public_document_detail(
    slug: str,
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Retrieve metadata and view parameters for a single published document."""
    svc = PublicSiteService(session)
    try:
        site, _ = await svc.get_published_website(slug)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Public portal '{slug}' not found.")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # Verify public membership
    is_public = await svc.verify_document_public_access(site.id, document_id)
    if not is_public:
        raise HTTPException(status_code=404, detail="Document not found or private.")

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
    }


@router.get("/sites/{slug}/documents/{document_id}/file")
async def stream_public_document_file(
    slug: str,
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    """Stream PDF or image file securely with strict visibility verification."""
    svc = PublicSiteService(session)
    try:
        site, _ = await svc.get_published_website(slug)
    except (ValueError, PermissionError):
        raise HTTPException(status_code=404, detail="Document portal not accessible.")

    is_public = await svc.verify_document_public_access(site.id, document_id)
    if not is_public:
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
    svc = PublicSiteService(session)
    try:
        site, _ = await svc.get_published_website(slug)
    except (ValueError, PermissionError):
        raise HTTPException(status_code=404, detail="Document portal not accessible.")

    is_public = await svc.verify_document_public_access(site.id, document_id)
    if not is_public:
        raise HTTPException(status_code=404, detail="Document not found or private.")

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
        doc = await session.get(Document, document_id)
        if doc:
            thumb_path = storage.get_local_path(doc.storage_path)

    if not thumb_path or not thumb_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found.")

    return FileResponse(
        path=str(thumb_path),
        media_type="image/png",
    )
