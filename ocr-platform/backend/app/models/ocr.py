"""OCR job, result, page, and word models."""
from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class OCRJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """An async OCR processing job.

    Status: pending → running → completed | failed
    """

    __tablename__ = "ocr_jobs"

    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    provider: Mapped[str] = mapped_column(String(100), nullable=False, default="tesseract")
    provider_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language: Mapped[str] = mapped_column(String(50), nullable=False, default="eng")
    options_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    preprocessing_profile: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    requested_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class OCRResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Full OCR result for a document — all pages combined."""

    __tablename__ = "ocr_results"

    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("ocr_jobs.id", ondelete="SET NULL"), nullable=True
    )
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    full_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Composite cache key (file_hash + provider + language + options + preprocessing)
    cache_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    pages: Mapped[list[OCRPage]] = relationship(
        "OCRPage", back_populates="ocr_result", cascade="all, delete-orphan"
    )


class OCRPage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """OCR output for a single page."""

    __tablename__ = "ocr_pages"

    ocr_result_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ocr_results.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)

    ocr_result: Mapped[OCRResult] = relationship("OCRResult", back_populates="pages")
    words: Mapped[list[OCRWord]] = relationship(
        "OCRWord", back_populates="page", cascade="all, delete-orphan"
    )


class OCRWord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Word-level OCR output with bounding box and confidence score."""

    __tablename__ = "ocr_words"

    page_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ocr_pages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_x: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_y: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    word_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    block_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    page: Mapped[OCRPage] = relationship("OCRPage", back_populates="words")
