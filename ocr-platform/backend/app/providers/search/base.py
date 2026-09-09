"""Search provider protocol and shared search data contracts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class SearchHit:
    """A single document hit in search results."""
    document_id: str
    title: str
    drawing_number: str | None
    score: float
    rank_tier: str  # exact_title | prefix_title | structured_field | ocr_text
    structured_fields: dict[str, Any] = field(default_factory=dict)
    snippet: str | None = None
    thumbnail_url: str | None = None


@dataclass
class SearchResult:
    """Paginated search response."""
    total: int
    page: int
    page_size: int
    total_pages: int
    hits: list[SearchHit] = field(default_factory=list)


@runtime_checkable
class SearchProvider(Protocol):
    """Protocol that all search index backends must implement."""

    async def index_document(
        self,
        document_id: str,
        website_id: str,
        title: str | None,
        drawing_number: str | None,
        full_text: str | None,
        structured_fields: dict[str, Any],
    ) -> None:
        """Index or update a document in the search index."""
        ...

    async def search(
        self,
        website_id: str,
        query: str | None = None,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "relevance",  # relevance | title | date | newest
    ) -> SearchResult:
        """Execute a search with ranking, filters, and pagination."""
        ...

    async def remove_document(self, document_id: str, website_id: str) -> None:
        """Remove a document from the search index."""
        ...
