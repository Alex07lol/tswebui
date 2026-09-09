"""Website, WebsiteVersion, WebsitePage, WebsiteCollection, and DocumentVisibility models."""
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Website(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Represents a public document portal website generated from an extraction Setup."""

    __tablename__ = "websites"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    setup_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("configurations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="draft"
    )  # draft | preview | published | unpublished | archived
    current_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    published_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    versions: Mapped[list[WebsiteVersion]] = relationship(
        "WebsiteVersion", back_populates="website", cascade="all, delete-orphan"
    )
    collections: Mapped[list[WebsiteCollection]] = relationship(
        "WebsiteCollection", back_populates="website", cascade="all, delete-orphan"
    )


class WebsiteVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """An immutable version snapshot of a published or in-draft website configuration."""

    __tablename__ = "website_versions"

    website_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="draft"
    )  # draft | published | archived
    site_title: Mapped[str] = mapped_column(String(255), nullable=False)
    tagline: Mapped[str | None] = mapped_column(String(500), nullable=True)
    header_logo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    theme_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    search_config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    field_mappings_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_view_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    bindings_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    actions_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    conditions_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    computed_fields_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    change_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    website: Mapped[Website] = relationship("Website", back_populates="versions")
    pages: Mapped[list[WebsitePage]] = relationship(
        "WebsitePage", back_populates="version", cascade="all, delete-orphan"
    )


class WebsitePage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Defines a page in a website version (e.g. Home, Search, DocumentDetail, About)."""

    __tablename__ = "website_pages"

    version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("website_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="home"
    )  # home | search | document | collection | about
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    layout_config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    components_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    version: Mapped[WebsiteVersion] = relationship("WebsiteVersion", back_populates="pages")


class WebsiteCollection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Organizes documents into curated collections based on metadata queries or categories."""

    __tablename__ = "website_collections"

    website_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    filter_query_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    website: Mapped[Website] = relationship("Website", back_populates="collections")


class DocumentVisibility(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Explicit publish gate for documents associated with a website."""

    __tablename__ = "document_visibilities"

    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    website_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
