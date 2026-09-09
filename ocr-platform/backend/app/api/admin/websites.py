"""Admin API endpoints for managing Universal Websites, Versions, Publications, and Document Membership."""
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

from app.api.admin.dependencies import require_admin_user
from app.core.database import get_session
from app.models.audit import AuditLog
from app.models.configuration import Configuration, ConfigurationVersion, ExtractionField
from app.models.data import DataSource, WebsiteDataSource, WebsiteDocument
from app.models.document import Document
from app.models.user import User
from app.models.website import (
    DocumentVisibility,
    Website,
    WebsiteCollection,
    WebsitePage,
    WebsiteVersion,
)
from app.services.data.data_source_service import DataSourceService
from app.services.search.indexer import SearchIndexer

router = APIRouter(dependencies=[Depends(require_admin_user)])


class CreateWebsiteRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str | None = None
    description: str | None = None
    setup_id: str | None = None
    data_source_id: str | None = None
    theme: dict[str, Any] | None = None
    search_config: dict[str, Any] | None = None
    field_mappings: dict[str, Any] | None = None
    document_view: dict[str, Any] | None = None
    bindings: dict[str, Any] | None = None
    actions: dict[str, Any] | None = None
    conditions: dict[str, Any] | None = None
    computed_fields: dict[str, Any] | None = None


class UpdateWebsiteRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    setup_id: str | None = None
    data_source_id: str | None = None
    theme: dict[str, Any] | None = None
    search_config: dict[str, Any] | None = None
    field_mappings: dict[str, Any] | None = None
    document_view: dict[str, Any] | None = None
    bindings: dict[str, Any] | None = None
    actions: dict[str, Any] | None = None
    conditions: dict[str, Any] | None = None
    computed_fields: dict[str, Any] | None = None
    pages: list[dict[str, Any]] | None = None


class CreateCollectionRequest(BaseModel):
    name: str
    slug: str | None = None
    description: str | None = None
    filter_query: dict[str, Any] | None = None
    display_order: int = 0


class AddDocumentMembershipRequest(BaseModel):
    document_ids: list[str]
    is_included: bool = True
    is_public: bool = True


class UpdateDocumentMembershipRequest(BaseModel):
    is_included: bool | None = None
    is_public: bool | None = None


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "-", cleaned)


@router.post("/websites")
async def create_website(
    payload: CreateWebsiteRequest,
    session: AsyncSession = Depends(get_session),
    admin_user: User = Depends(require_admin_user),
) -> dict[str, Any]:
    """Create a new universal website with draft version snapshot."""
    slug = _slugify(payload.slug or payload.name)
    if not slug:
        slug = f"site-{uuid.uuid4().hex[:6]}"

    # Check slug uniqueness
    existing = (await session.execute(select(Website).where(Website.slug == slug))).scalars().first()
    if existing:
        slug = f"{slug}-{uuid.uuid4().hex[:4]}"

    site_id = str(uuid.uuid4())
    version_id = str(uuid.uuid4())

    # If setup_id provided, ensure a synced DataSource exists
    ds_id = payload.data_source_id
    if payload.setup_id and not ds_id:
        ds_svc = DataSourceService(session)
        ds = await ds_svc.sync_setup_to_data_source(payload.setup_id)
        if ds:
            ds_id = ds.id

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
        "badge_fields": ["project", "revision"],
        "metadata_fields": ["title", "drawing_number", "project", "date"],
    }

    # Default Document View
    document_view = payload.document_view or {
        "show_pdf_viewer": True,
        "allow_download": True,
        "show_thumbnails": True,
    }

    initial_version = WebsiteVersion(
        id=version_id,
        website_id=site_id,
        version_number=1,
        status="draft",
        site_title=payload.name,
        tagline=f"Searchable portal for {payload.name}",
        theme_json=json.dumps(theme),
        search_config_json=json.dumps(search_config),
        field_mappings_json=json.dumps(field_mappings),
        document_view_json=json.dumps(document_view),
        bindings_json=json.dumps(payload.bindings or {}),
        actions_json=json.dumps(payload.actions or {}),
        conditions_json=json.dumps(payload.conditions or {}),
        computed_fields_json=json.dumps(payload.computed_fields or {}),
        change_notes="Initial draft creation",
    )

    website = Website(
        id=site_id,
        name=payload.name,
        slug=slug,
        description=payload.description,
        setup_id=payload.setup_id,
        status="draft",
        current_version_id=version_id,
        published_version_id=None,
        created_by=admin_user.id if admin_user else None,
    )

    session.add(website)
    session.add(initial_version)

    # Link DataSource if available
    if ds_id:
        session.add(
            WebsiteDataSource(
                id=str(uuid.uuid4()),
                website_id=site_id,
                data_source_id=ds_id,
                default_source=True,
            )
        )

    # Add default pages
    session.add(
        WebsitePage(
            id=str(uuid.uuid4()),
            version_id=version_id,
            page_type="home",
            title="Home",
            slug="",
            display_order=1,
        )
    )
    session.add(
        WebsitePage(
            id=str(uuid.uuid4()),
            version_id=version_id,
            page_type="search",
            title="Search Documents",
            slug="search",
            display_order=2,
        )
    )

    # Audit Log
    session.add(
        AuditLog(
            id=str(uuid.uuid4()),
            event_type="website.created",
            resource_type="website",
            resource_id=site_id,
            details_json=json.dumps({"name": payload.name, "slug": slug}),
        )
    )

    await session.commit()

    return {
        "id": website.id,
        "name": website.name,
        "slug": website.slug,
        "status": website.status,
        "setup_id": website.setup_id,
        "data_source_id": ds_id,
        "version_number": 1,
        "created_at": website.created_at.isoformat() if website.created_at else None,
    }


@router.get("/websites")
async def list_websites(
    session: AsyncSession = Depends(get_session),
    admin_user: User = Depends(require_admin_user),
) -> list[dict[str, Any]]:
    """List all universal websites."""
    stmt = (
        select(Website)
        .options(selectinload(Website.versions), selectinload(Website.collections))
        .order_by(desc(Website.created_at))
    )
    sites = (await session.execute(stmt)).scalars().all()

    out = []
    for s in sites:
        latest_ver = s.versions[-1] if s.versions else None
        published_ver = next((v for v in s.versions if v.id == s.published_version_id), None)
        out.append({
            "id": s.id,
            "name": s.name,
            "slug": s.slug,
            "description": s.description,
            "setup_id": s.setup_id,
            "status": s.status,
            "version_number": latest_ver.version_number if latest_ver else 1,
            "published_version": published_ver.version_number if published_ver else None,
            "collection_count": len(s.collections),
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        })
    return out


@router.get("/websites/{site_id}")
async def get_website(
    site_id: str,
    session: AsyncSession = Depends(get_session),
    admin_user: User = Depends(require_admin_user),
) -> dict[str, Any]:
    """Retrieve full configuration details for a website draft/version."""
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
    bindings = json.loads(latest_ver.bindings_json) if latest_ver and latest_ver.bindings_json else {}
    actions = json.loads(latest_ver.actions_json) if latest_ver and latest_ver.actions_json else {}
    conditions = json.loads(latest_ver.conditions_json) if latest_ver and latest_ver.conditions_json else {}
    computed_fields = json.loads(latest_ver.computed_fields_json) if latest_ver and latest_ver.computed_fields_json else {}

    pages = []
    if latest_ver and latest_ver.pages:
        for p in latest_ver.pages:
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
        "id": site.id,
        "name": site.name,
        "slug": site.slug,
        "description": site.description,
        "setup_id": site.setup_id,
        "status": site.status,
        "version_number": latest_ver.version_number if latest_ver else 1,
        "published_version_id": site.published_version_id,
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
                "id": c.id,
                "name": c.name,
                "slug": c.slug,
                "description": c.description,
                "filter_query": json.loads(c.filter_query_json) if c.filter_query_json else {},
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
    admin_user: User = Depends(require_admin_user),
) -> dict[str, Any]:
    """Update website configuration.
    
    CRITICAL INVARIANT: If the active version is published, an immutable published snapshot
    must be preserved and a NEW draft version branched. Live public sites are never directly modified.
    """
    stmt = (
        select(Website)
        .options(
            selectinload(Website.versions).selectinload(WebsiteVersion.pages),
        )
        .where(Website.id == site_id)
    )
    site = (await session.execute(stmt)).scalars().first()
    if not site:
        raise HTTPException(status_code=404, detail="Website not found.")

    if payload.name:
        site.name = payload.name
    if payload.description is not None:
        site.description = payload.description
    if payload.setup_id is not None:
        site.setup_id = payload.setup_id

    current_ver = site.versions[-1] if site.versions else None

    # Draft branching rule: If current version is published, branch to a new draft version
    if current_ver and current_ver.status == "published":
        new_version_number = current_ver.version_number + 1
        new_ver_id = str(uuid.uuid4())
        target_ver = WebsiteVersion(
            id=new_ver_id,
            website_id=site.id,
            version_number=new_version_number,
            status="draft",
            site_title=site.name,
            tagline=current_ver.tagline,
            header_logo=current_ver.header_logo,
            theme_json=current_ver.theme_json,
            search_config_json=current_ver.search_config_json,
            field_mappings_json=current_ver.field_mappings_json,
            document_view_json=current_ver.document_view_json,
            bindings_json=current_ver.bindings_json,
            actions_json=current_ver.actions_json,
            conditions_json=current_ver.conditions_json,
            computed_fields_json=current_ver.computed_fields_json,
            change_notes=f"Draft branched from v{current_ver.version_number}",
        )
        session.add(target_ver)

        # Clone pages to new draft
        for p in current_ver.pages:
            session.add(
                WebsitePage(
                    id=str(uuid.uuid4()),
                    version_id=new_ver_id,
                    page_type=p.page_type,
                    title=p.title,
                    slug=p.slug,
                    layout_config_json=p.layout_config_json,
                    components_json=p.components_json,
                    display_order=p.display_order,
                )
            )

        site.current_version_id = new_ver_id
    else:
        target_ver = current_ver

    # Apply configuration updates to the target draft version
    if target_ver:
        if payload.theme is not None:
            target_ver.theme_json = json.dumps(payload.theme)
        if payload.search_config is not None:
            target_ver.search_config_json = json.dumps(payload.search_config)
        if payload.field_mappings is not None:
            target_ver.field_mappings_json = json.dumps(payload.field_mappings)
        if payload.document_view is not None:
            target_ver.document_view_json = json.dumps(payload.document_view)
        if payload.bindings is not None:
            target_ver.bindings_json = json.dumps(payload.bindings)
        if payload.actions is not None:
            target_ver.actions_json = json.dumps(payload.actions)
        if payload.conditions is not None:
            target_ver.conditions_json = json.dumps(payload.conditions)
        if payload.computed_fields is not None:
            target_ver.computed_fields_json = json.dumps(payload.computed_fields)
        if payload.pages is not None:
            from sqlalchemy import delete
            await session.execute(delete(WebsitePage).where(WebsitePage.version_id == target_ver.id))
            for idx, page_data in enumerate(payload.pages):
                session.add(
                    WebsitePage(
                        id=page_data.get("id") or str(uuid.uuid4()),
                        version_id=target_ver.id,
                        page_type=page_data.get("page_type", "custom"),
                        title=page_data.get("title", f"Page {idx+1}"),
                        slug=page_data.get("slug", f"page-{idx+1}"),
                        layout_config_json=json.dumps(page_data.get("layout_config", {})),
                        components_json=json.dumps(page_data.get("components", [])),
                        display_order=page_data.get("display_order", idx),
                    )
                )

    site.updated_at = datetime.now(timezone.utc)
    await session.commit()

    return {
        "status": "ok",
        "id": site.id,
        "name": site.name,
        "version_number": target_ver.version_number if target_ver else 1,
        "version_status": target_ver.status if target_ver else "draft",
    }


@router.delete("/websites/{site_id}")
async def delete_website(
    site_id: str,
    session: AsyncSession = Depends(get_session),
    admin_user: User = Depends(require_admin_user),
) -> dict[str, Any]:
    """Delete a website and its associated versions and memberships."""
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
    admin_user: User = Depends(require_admin_user),
) -> dict[str, Any]:
    """Publish draft website version: freezes immutable snapshot and indexes explicit public document members."""
    stmt = (
        select(Website)
        .options(
            selectinload(Website.versions),
            selectinload(Website.collections),
        )
        .where(Website.id == site_id)
    )
    site = (await session.execute(stmt)).scalars().first()
    if not site:
        raise HTTPException(status_code=404, detail="Website not found.")

    draft_ver = site.versions[-1] if site.versions else None
    if not draft_ver:
        raise HTTPException(status_code=400, detail="Website has no version to publish.")

    # Archive previous published versions
    now = datetime.now(timezone.utc)
    for v in site.versions:
        if v.id != draft_ver.id and v.status == "published":
            v.status = "archived"

    draft_ver.status = "published"
    draft_ver.published_at = now
    site.status = "published"
    site.published_version_id = draft_ver.id
    site.current_version_id = draft_ver.id
    site.updated_at = now

    # Index ONLY explicit WebsiteDocument members marked public (Rule G & H)
    indexer = SearchIndexer(session)
    indexed_count = await indexer.index_all_documents_for_website(site.id, make_public=True)

    # Audit Log
    session.add(
        AuditLog(
            id=str(uuid.uuid4()),
            event_type="website.published",
            resource_type="website",
            resource_id=site.id,
            details_json=json.dumps({
                "version_number": draft_ver.version_number,
                "version_id": draft_ver.id,
                "indexed_documents": indexed_count,
            }),
        )
    )

    await session.commit()

    return {
        "status": "published",
        "website_id": site.id,
        "slug": site.slug,
        "published_version": draft_ver.version_number,
        "indexed_documents": indexed_count,
        "published_at": now.isoformat(),
        "public_url": f"http://localhost:5174/{site.slug}",
    }


@router.post("/websites/{site_id}/unpublish")
async def unpublish_website(
    site_id: str,
    session: AsyncSession = Depends(get_session),
    admin_user: User = Depends(require_admin_user),
) -> dict[str, Any]:
    """Take a published website offline."""
    site = await session.get(Website, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Website not found.")

    site.status = "unpublished"
    site.updated_at = datetime.now(timezone.utc)

    # Audit Log
    session.add(
        AuditLog(
            id=str(uuid.uuid4()),
            event_type="website.unpublished",
            resource_type="website",
            resource_id=site.id,
            details_json=json.dumps({"slug": site.slug}),
        )
    )

    await session.commit()
    return {"status": "unpublished", "website_id": site.id}


@router.post("/websites/{site_id}/collections")
async def add_collection(
    site_id: str,
    payload: CreateCollectionRequest,
    session: AsyncSession = Depends(get_session),
    admin_user: User = Depends(require_admin_user),
) -> dict[str, Any]:
    """Add a queryable collection category to a website."""
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


# --- Explicit Document Membership Management (P0 Rules H & I) ---


@router.get("/websites/{site_id}/documents")
async def list_website_documents(
    site_id: str,
    session: AsyncSession = Depends(get_session),
    admin_user: User = Depends(require_admin_user),
) -> list[dict[str, Any]]:
    """List all documents explicitly associated with a website."""
    stmt = (
        select(WebsiteDocument, Document)
        .join(Document, WebsiteDocument.document_id == Document.id)
        .where(WebsiteDocument.website_id == site_id)
        .order_by(WebsiteDocument.display_order.asc())
    )
    results = (await session.execute(stmt)).all()

    out = []
    for wd, doc in results:
        out.append({
            "membership_id": wd.id,
            "document_id": doc.id,
            "filename": doc.original_filename,
            "is_included": wd.is_included,
            "is_public": wd.is_public,
            "display_order": wd.display_order,
            "published_at": wd.published_at.isoformat() if wd.published_at else None,
        })
    return out


@router.post("/websites/{site_id}/documents")
async def add_website_documents(
    site_id: str,
    payload: AddDocumentMembershipRequest,
    session: AsyncSession = Depends(get_session),
    admin_user: User = Depends(require_admin_user),
) -> dict[str, Any]:
    """Explicitly assign documents to website membership with public visibility flags."""
    site = await session.get(Website, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Website not found.")

    now = datetime.now(timezone.utc)
    added_count = 0
    indexer = SearchIndexer(session)

    for doc_id in payload.document_ids:
        # Check existing membership
        existing = (
            await session.execute(
                select(WebsiteDocument).where(
                    WebsiteDocument.website_id == site_id,
                    WebsiteDocument.document_id == doc_id,
                )
            )
        ).scalars().first()

        if not existing:
            wd = WebsiteDocument(
                id=str(uuid.uuid4()),
                website_id=site_id,
                document_id=doc_id,
                is_included=payload.is_included,
                is_public=payload.is_public,
                published_at=now if payload.is_public else None,
            )
            session.add(wd)
            added_count += 1
        else:
            existing.is_included = payload.is_included
            existing.is_public = payload.is_public
            if payload.is_public and not existing.published_at:
                existing.published_at = now

        # Also sync DocumentVisibility
        vis = (
            await session.execute(
                select(DocumentVisibility).where(
                    DocumentVisibility.website_id == site_id,
                    DocumentVisibility.document_id == doc_id,
                )
            )
        ).scalars().first()
        if not vis:
            vis = DocumentVisibility(
                id=str(uuid.uuid4()),
                website_id=site_id,
                document_id=doc_id,
                is_public=payload.is_public,
                published_at=now if payload.is_public else None,
            )
            session.add(vis)
        else:
            vis.is_public = payload.is_public

        # If website is already published and doc is public, index it immediately
        if site.status == "published" and payload.is_public:
            await indexer.index_document_for_website(doc_id, site_id, make_public=True)

    await session.commit()
    return {"status": "ok", "added_count": added_count}


@router.patch("/websites/{site_id}/documents/{doc_id}")
async def update_website_document_status(
    site_id: str,
    doc_id: str,
    payload: UpdateDocumentMembershipRequest,
    session: AsyncSession = Depends(get_session),
    admin_user: User = Depends(require_admin_user),
) -> dict[str, Any]:
    """Toggle document inclusion and public visibility for a website."""
    stmt = select(WebsiteDocument).where(
        WebsiteDocument.website_id == site_id,
        WebsiteDocument.document_id == doc_id,
    )
    wd = (await session.execute(stmt)).scalars().first()
    if not wd:
        raise HTTPException(status_code=404, detail="Document membership not found.")

    if payload.is_included is not None:
        wd.is_included = payload.is_included
    if payload.is_public is not None:
        wd.is_public = payload.is_public
        if wd.is_public:
            wd.published_at = datetime.now(timezone.utc)
            # Sync to search index
            indexer = SearchIndexer(session)
            await indexer.index_document_for_website(doc_id, site_id, make_public=True)

    # Sync to DocumentVisibility
    vis = (
        await session.execute(
            select(DocumentVisibility).where(
                DocumentVisibility.website_id == site_id,
                DocumentVisibility.document_id == doc_id,
            )
        )
    ).scalars().first()
    if vis and payload.is_public is not None:
        vis.is_public = payload.is_public

    await session.commit()
    return {"status": "ok", "document_id": doc_id, "is_public": wd.is_public}


@router.post("/websites/{site_id}/documents/sync-from-setup")
async def sync_documents_from_setup(
    site_id: str,
    make_public: bool = Query(False, description="Default to public visibility for imported documents"),
    session: AsyncSession = Depends(get_session),
    admin_user: User = Depends(require_admin_user),
) -> dict[str, Any]:
    """Import documents processed under the website's linked setup into explicit website membership."""
    site = await session.get(Website, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Website not found.")
    if not site.setup_id:
        raise HTTPException(status_code=400, detail="Website has no linked Setup.")

    # Find documents with ready status
    doc_stmt = select(Document.id).where(Document.status == "ready")
    doc_ids = (await session.execute(doc_stmt)).scalars().all()

    added_count = 0
    now = datetime.now(timezone.utc)
    for did in doc_ids:
        existing = (
            await session.execute(
                select(WebsiteDocument).where(
                    WebsiteDocument.website_id == site_id,
                    WebsiteDocument.document_id == did,
                )
            )
        ).scalars().first()
        if not existing:
            wd = WebsiteDocument(
                id=str(uuid.uuid4()),
                website_id=site_id,
                document_id=did,
                is_included=True,
                is_public=make_public,
                published_at=now if make_public else None,
            )
            session.add(wd)
            added_count += 1

    await session.commit()
    return {"status": "ok", "imported_count": added_count}
