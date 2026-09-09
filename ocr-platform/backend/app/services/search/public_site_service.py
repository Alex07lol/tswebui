"""Public Site Service: orchestrates search, collections, document access, and visibility enforcement."""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.data import WebsiteDocument
from app.models.document import Document
from app.models.locator import SearchIndexMetadata
from app.models.website import DocumentVisibility, Website, WebsiteCollection, WebsiteVersion
from app.providers.search.database import DatabaseSearchProvider, SearchResult


class PublicSiteService:
    """Service layer for public portal requests ensuring strict publication boundaries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.search_provider = DatabaseSearchProvider(session)

    async def get_published_website(self, slug: str) -> tuple[Website, WebsiteVersion]:
        """Resolve a published website by slug and return its immutable published version snapshot."""
        stmt = (
            select(Website)
            .options(
                selectinload(Website.versions).selectinload(WebsiteVersion.pages),
                selectinload(Website.collections),
            )
            .where(Website.slug == slug)
        )
        site = (await self.session.execute(stmt)).scalars().first()
        if not site:
            raise ValueError(f"Public portal '{slug}' not found.")
        if site.status != "published":
            raise PermissionError("This document portal is currently offline or unpublished.")

        # Resolve immutable published snapshot
        pub_ver = None
        if site.published_version_id:
            pub_ver = next((v for v in site.versions if v.id == site.published_version_id and v.status == "published"), None)
        if not pub_ver:
            pub_ver = next((v for v in reversed(site.versions) if v.status == "published"), None)

        if not pub_ver:
            raise PermissionError("This document portal has no published version available.")

        return site, pub_ver

    async def list_published_websites(self) -> list[dict[str, Any]]:
        """List all published websites for discovery without leaking draft details."""
        stmt = (
            select(Website)
            .options(selectinload(Website.versions))
            .where(Website.status == "published")
        )
        sites = (await self.session.execute(stmt)).scalars().all()

        out = []
        for s in sites:
            pub_ver = next((v for v in s.versions if v.id == s.published_version_id and v.status == "published"), None)
            if not pub_ver:
                pub_ver = next((v for v in reversed(s.versions) if v.status == "published"), None)
            if not pub_ver:
                continue

            theme = json.loads(pub_ver.theme_json) if pub_ver.theme_json else {}
            out.append({
                "name": s.name,
                "slug": s.slug,
                "description": s.description,
                "site_title": pub_ver.site_title,
                "tagline": pub_ver.tagline,
                "header_logo": pub_ver.header_logo,
                "theme": theme,
            })
        return out

    async def execute_search(
        self,
        website_id: str,
        query: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "relevance",
        field_filters: dict[str, Any] | None = None,
    ) -> SearchResult:
        """Search published documents via the search provider."""
        return await self.search_provider.search(
            website_id=website_id,
            query=query,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            field_filters=field_filters,
        )

    async def get_collection_documents(
        self,
        website_id: str,
        collection: WebsiteCollection,
        page: int = 1,
        page_size: int = 20,
    ) -> SearchResult:
        """Query documents matching a collection's configured filter query."""
        filter_query = json.loads(collection.filter_query_json) if collection.filter_query_json else {}
        field_filters = {}
        if "field" in filter_query and "value" in filter_query:
            field_filters[filter_query["field"]] = filter_query["value"]

        return await self.search_provider.search(
            website_id=website_id,
            query=filter_query.get("search_term"),
            page=page,
            page_size=page_size,
            field_filters=field_filters if field_filters else None,
        )

    async def verify_document_public_access(self, website_id: str, document_id: str) -> bool:
        """Verify that a document is explicitly published and public for this website."""
        # 1. Check WebsiteDocument
        wd_stmt = select(WebsiteDocument).where(
            WebsiteDocument.website_id == website_id,
            WebsiteDocument.document_id == document_id,
            WebsiteDocument.is_included == True,
            WebsiteDocument.is_public == True,
        )
        wd = (await self.session.execute(wd_stmt)).scalars().first()
        if wd:
            return True

        # 2. Check DocumentVisibility fallback
        vis_stmt = select(DocumentVisibility).where(
            DocumentVisibility.website_id == website_id,
            DocumentVisibility.document_id == document_id,
            DocumentVisibility.is_public == True,
        )
        vis = (await self.session.execute(vis_stmt)).scalars().first()
        return bool(vis)
