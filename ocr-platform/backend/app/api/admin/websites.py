"""Admin API endpoints for managing Document Websites, Versions, and Publications."""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models.audit import AuditLog
from app.models.configuration import Configuration, ConfigurationVersion, ExtractionField
from app.models.website import (
    DocumentVisibility,
    Website,
    WebsiteCollection,
    WebsitePage,
    WebsiteVersion,
)
from app.services.search.indexer import SearchIndexer

router = APIRouter()


class CreateWebsiteRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str | None = None
    description: str | None = None
    setup_id: str | None = None
    theme: dict[str, Any] | None = None
    search_config: dict[str, Any] | None = None
    field_mappings: dict[str, Any] | None = None
    document_view: dict[str, Any] | None = None


class UpdateWebsiteRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    setup_id: str | None = None
    theme: dict[str, Any] | None = None
    search_config: dict[str, Any] | None = None
    field_mappings: dict[str, Any] | None = None
    document_view: dict[str, Any] | None = None


class CreateCollectionRequest(BaseModel):
    name: str
    slug: str | None = None
    description: str | None = None
    filter_query: dict[str, Any] | None = None
    display_order: int = 0


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "-", cleaned)


@router.post("/websites")
async def create_website(
    payload: CreateWebsiteRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Create a new document website tied to an extraction setup."""
    slug = _slugify(payload.slug or payload.name)
    if not slug:
        slug = f"site-{uuid.uuid4().hex[:6]}"

    # Check slug uniqueness
    existing = (await session.execute(select(Website).where(Website.slug == slug))).scalars().first()
    if existing:
        slug = f"{slug}-{uuid.uuid4().hex[:4]}"

    site_id = str(uuid.uuid4())
    version_id = str(uuid.uuid4())

    # Default Theme
    theme = payload.theme or {
        "preset": "engineering_dark",
        "primary_color": "#2563eb",
        "accent_color": "#38bdf8",
        "background": "#0f172a",
        "font_family": "Inter, sans-serif",
    }

    # Default Search Configuration
    search_config = payload.search_config or {
        "searchable_fields": ["title", "drawing_number", "project", "date"],
        "enable_fuzzy": True,
        "default_sort": "relevance",
    }

    # Default Field Mappings
    field_mappings = payload.field_mappings or {
        "title_field": "title",
        "drawing_number_field": "drawing_number",
        "badge_fields": ["revision", "project"],
        "metadata_fields": ["title", "drawing_number", "revision", "project", "date"],
    }

    # Default Document View
    document_view = payload.document_view or {
        "show_pdf_viewer": True,
        "allow_download": True,
        "show_thumbnails": True,
    }

    # Create Initial Version
    initial_version = WebsiteVersion(
        id=version_id,
        website_id=site_id,
        version_number=1,
        status="draft",
        site_title=payload.name,
        tagline=f"Public document archive for {payload.name}",
        theme_json=json.dumps(theme),
        search_config_json=json.dumps(search_config),
        field_mappings_json=json.dumps(field_mappings),
        document_view_json=json.dumps(document_view),
        change_notes="Initial creation",
    )

    website = Website(
        id=site_id,
        name=payload.name,
        slug=slug,
        description=payload.description,
        setup_id=payload.setup_id,
        status="draft",
        current_version_id=version_id,
    )

    session.add(website)
    session.add(initial_version)

    # Add default pages
    session.add(WebsitePage(
        id=str(uuid.uuid4()),
        version_id=version_id,
        page_type="home",
        title="Home",
        slug="",
        display_order=1,
    ))
    session.add(WebsitePage(
        id=str(uuid.uuid4()),
        version_id=version_id,
        page_type="search",
        title="Search Documents",
        slug="search",
        display_order=2,
    ))

    # Audit Log
    session.add(AuditLog(
        id=str(uuid.uuid4()),
        event_type="website.created",
        resource_type="website",
        resource_id=site_id,
        details_json=json.dumps({"name": payload.name, "slug": slug}),
    ))

    await session.commit()

    return {
        "id": website.id,
        "name": website.name,
        "slug": website.slug,
        "status": website.status,
        "setup_id": website.setup_id,
        "version_number": 1,
        "created_at": website.created_at.isoformat() if website.created_at else None,
    }


@router.get("/websites")
async def list_websites(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """List all document websites."""
    stmt = (
        select(Website)
        .options(selectinload(Website.versions), selectinload(Website.collections))
        .order_by(desc(Website.created_at))
    )
    sites = (await session.execute(stmt)).scalars().all()

    out = []
    for s in sites:
        latest_ver = s.versions[-1] if s.versions else None
        out.append({
            "id": s.id,
            "name": s.name,
            "slug": s.slug,
            "description": s.description,
            "setup_id": s.setup_id,
            "status": s.status,
            "version_number": latest_ver.version_number if latest_ver else 1,
            "collection_count": len(s.collections),
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        })
    return out


@router.get("/websites/{site_id}")
async def get_website(
    site_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Retrieve full configuration details for a website."""
    stmt = (
        select(Website)
        .options(
            selectinload(Website.versions).selectinload(WebsiteVersion.pages),
            selectinload(Website.collections),
        )
        .where(Website.id == site_id)
    )
    site = (await session.execute(stmt)).scalars().first()
    if not site:
        raise HTTPException(status_code=404, detail=f"Website '{site_id}' not found.")

    latest_ver = site.versions[-1] if site.versions else None

    theme = json.loads(latest_ver.theme_json) if latest_ver and latest_ver.theme_json else {}
    search_config = json.loads(latest_ver.search_config_json) if latest_ver and latest_ver.search_config_json else {}
    field_mappings = json.loads(latest_ver.field_mappings_json) if latest_ver and latest_ver.field_mappings_json else {}
    document_view = json.loads(latest_ver.document_view_json) if latest_ver and latest_ver.document_view_json else {}

    return {
        "id": site.id,
        "name": site.name,
        "slug": site.slug,
        "description": site.description,
        "setup_id": site.setup_id,
        "status": site.status,
        "version_number": latest_ver.version_number if latest_ver else 1,
        "theme": theme,
        "search_config": search_config,
        "field_mappings": field_mappings,
        "document_view": document_view,
        "collections": [
            {
                "id": c.id,
                "name": c.name,
                "slug": c.slug,
                "description": c.description,
                "display_order": c.display_order,
            }
            for c in site.collections
        ],
        "created_at": site.created_at.isoformat() if site.created_at else None,
        "updated_at": site.updated_at.isoformat() if site.updated_at else None,
    }


@router.put("/websites/{site_id}")
async def update_website(
    site_id: str,
    payload: UpdateWebsiteRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Update website settings and draft version configuration."""
    stmt = select(Website).options(selectinload(Website.versions)).where(Website.id == site_id)
    site = (await session.execute(stmt)).scalars().first()
    if not site:
        raise HTTPException(status_code=404, detail="Website not found.")

    if payload.name:
        site.name = payload.name
    if payload.description is not None:
        site.description = payload.description
    if payload.setup_id is not None:
        site.setup_id = payload.setup_id

    # Update latest version config
    if site.versions:
        ver = site.versions[-1]
        if payload.theme is not None:
            ver.theme_json = json.dumps(payload.theme)
        if payload.search_config is not None:
            ver.search_config_json = json.dumps(payload.search_config)
        if payload.field_mappings is not None:
            ver.field_mappings_json = json.dumps(payload.field_mappings)
        if payload.document_view is not None:
            ver.document_view_json = json.dumps(payload.document_view)

    site.updated_at = datetime.now(timezone.utc)
    await session.commit()

    return {"status": "ok", "id": site.id, "name": site.name}


@router.delete("/websites/{site_id}")
async def delete_website(
    site_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Delete a document website and its associated versions."""
    site = await session.get(Website, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Website not found.")

    await session.delete(site)
    await session.commit()
    return {"status": "ok", "deleted_id": site_id}


@router.post("/websites/{site_id}/publish")
async def publish_website(
    site_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Publish the document website, freeze version snapshot, and populate search index."""
    stmt = select(Website).options(selectinload(Website.versions)).where(Website.id == site_id)
    site = (await session.execute(stmt)).scalars().first()
    if not site:
        raise HTTPException(status_code=404, detail="Website not found.")

    latest_ver = site.versions[-1] if site.versions else None
    if not latest_ver:
        raise HTTPException(status_code=400, detail="Website has no version to publish.")

    now = datetime.now(timezone.utc)
    latest_ver.status = "published"
    latest_ver.published_at = now
    site.status = "published"
    site.updated_at = now

    # Index all documents into SearchIndexMetadata
    indexer = SearchIndexer(session)
    indexed_count = await indexer.index_all_documents_for_website(site.id, make_public=True)

    # Audit Log
    session.add(AuditLog(
        id=str(uuid.uuid4()),
        event_type="website.published",
        resource_type="website",
        resource_id=site.id,
        details_json=json.dumps({"version_number": latest_ver.version_number, "indexed_documents": indexed_count}),
    ))

    await session.commit()

    return {
        "status": "published",
        "website_id": site.id,
        "slug": site.slug,
        "published_version": latest_ver.version_number,
        "indexed_documents": indexed_count,
        "published_at": now.isoformat(),
        "public_url": f"http://localhost:5174/{site.slug}",
    }


@router.post("/websites/{site_id}/unpublish")
async def unpublish_website(
    site_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Take a published website offline."""
    site = await session.get(Website, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Website not found.")

    site.status = "unpublished"
    site.updated_at = datetime.now(timezone.utc)

    # Audit Log
    session.add(AuditLog(
        id=str(uuid.uuid4()),
        event_type="website.unpublished",
        resource_type="website",
        resource_id=site.id,
        details_json=json.dumps({"slug": site.slug}),
    ))

    await session.commit()
    return {"status": "unpublished", "website_id": site.id}


@router.post("/websites/{site_id}/collections")
async def add_collection(
    site_id: str,
    payload: CreateCollectionRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Add a collection category to a website."""
    site = await session.get(Website, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Website not found.")

    c_slug = _slugify(payload.slug or payload.name)
    coll = WebsiteCollection(
        id=str(uuid.uuid4()),
        website_id=site.id,
        name=payload.name,
        slug=c_slug,
        description=payload.description,
        filter_query_json=json.dumps(payload.filter_query or {}),
        display_order=payload.display_order,
    )
    session.add(coll)
    await session.commit()
    return {"status": "ok", "collection_id": coll.id, "slug": coll.slug}
