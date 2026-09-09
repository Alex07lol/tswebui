"""Extraction locator, example, and search index models for visual PDF teaching."""
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ExtractionLocator(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Represents a visual, coordinate-aware, and structural locator for finding a field."""

    __tablename__ = "extraction_locators"

    field_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("extraction_fields.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    template_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    page_mode: Mapped[str] = mapped_column(
        String(50), nullable=False, default="first"
    )  # first | last | specific | all
    specific_page: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relative normalized coordinates (0.0 to 1.0)
    rel_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    rel_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    rel_width: Mapped[float | None] = mapped_column(Float, nullable=True)
    rel_height: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Context & anchor candidates (JSON list of anchor labels e.g. ["TITLE", "DRAWING TITLE"])
    anchor_candidates_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Structural configuration (JSON: same_line, line_offset, expected_type, word_count)
    structure_config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    pattern_value: Mapped[str | None] = mapped_column(String(500), nullable=True)

    tolerance_x: Mapped[float] = mapped_column(Float, nullable=False, default=0.08)
    tolerance_y: Mapped[float] = mapped_column(Float, nullable=False, default=0.05)
    confidence_weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    examples: Mapped[list[LocatorExample]] = relationship(
        "LocatorExample", back_populates="locator", cascade="all, delete-orphan"
    )


class LocatorExample(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """An annotated ground-truth example from a specific document that trained a locator."""

    __tablename__ = "locator_examples"

    locator_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("extraction_locators.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    selected_text: Mapped[str] = mapped_column(String(500), nullable=False)

    # Pixel coordinates on original page image
    bbox_x: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_y: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_width: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_height: Mapped[int] = mapped_column(Integer, nullable=False)
    page_width: Mapped[int] = mapped_column(Integer, nullable=False)
    page_height: Mapped[int] = mapped_column(Integer, nullable=False)

    nearby_labels_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    locator: Mapped[ExtractionLocator] = relationship("ExtractionLocator", back_populates="examples")


class SearchIndexMetadata(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Precomputed search index document entry for high-speed public portal search."""

    __tablename__ = "search_index_metadata"

    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    website_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    drawing_number: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    full_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    structured_fields_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
