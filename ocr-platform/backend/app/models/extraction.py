"""Extraction job and result models."""
from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ExtractionJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """An async job to extract structured data from a document."""

    __tablename__ = "extraction_jobs"

    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    config_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("configuration_versions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    requested_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class ExtractionResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Complete structured extraction result for a job."""

    __tablename__ = "extraction_results"

    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("extraction_jobs.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    config_version_id: Mapped[str] = mapped_column(String(36), nullable=False)
    overall_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    values: Mapped[list[ExtractedValue]] = relationship(
        "ExtractedValue", back_populates="result", cascade="all, delete-orphan"
    )


class ExtractedValue(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A single extracted field value with full provenance."""

    __tablename__ = "extracted_values"

    result_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("extraction_results.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    field_id: Mapped[str] = mapped_column(String(100), nullable=False)
    output_variable: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    validation_passed: Mapped[bool | None] = mapped_column(default=None)
    validation_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    result: Mapped[ExtractionResult] = relationship("ExtractionResult", back_populates="values")
    evidence: Mapped[list[ExtractionEvidence]] = relationship(
        "ExtractionEvidence", back_populates="extracted_value", cascade="all, delete-orphan"
    )


class ExtractionEvidence(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Evidence trace for an extracted value — which rule matched and where."""

    __tablename__ = "extraction_evidence"

    extracted_value_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("extracted_values.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    rule_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    anchor_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_line: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_x: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_y: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    extracted_value: Mapped[ExtractedValue] = relationship(
        "ExtractedValue", back_populates="evidence"
    )
