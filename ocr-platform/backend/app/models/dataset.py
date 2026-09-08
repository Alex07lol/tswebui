"""Dataset and dataset-document association models."""
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Dataset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A named collection of documents used for pattern learning."""

    __tablename__ = "datasets"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    documents: Mapped[list[DatasetDocument]] = relationship(
        "DatasetDocument", back_populates="dataset", cascade="all, delete-orphan"
    )


class DatasetDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Links a document to a dataset."""

    __tablename__ = "dataset_documents"

    dataset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    added_order: Mapped[int | None] = mapped_column(Integer, nullable=True)

    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="documents")
