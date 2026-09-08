"""Pattern discovery / learning run models."""
from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class DiscoveryRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A pattern-learning run executed against a dataset."""

    __tablename__ = "discovery_runs"

    dataset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    documents_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clusters_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    proposals_generated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    initiated_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    clusters: Mapped[list[DocumentCluster]] = relationship(
        "DocumentCluster", back_populates="run", cascade="all, delete-orphan"
    )


class DocumentCluster(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A cluster of structurally similar documents found during discovery."""

    __tablename__ = "document_clusters"

    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("discovery_runs.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    document_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_outlier: Mapped[bool] = mapped_column(default=False)
    fingerprint_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    run: Mapped[DiscoveryRun] = relationship("DiscoveryRun", back_populates="clusters")
    proposals: Mapped[list[PatternProposal]] = relationship(
        "PatternProposal", back_populates="cluster", cascade="all, delete-orphan"
    )


class PatternProposal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A system-generated field/rule proposal from pattern learning.

    Status: pending → approved | rejected | edited
    """

    __tablename__ = "pattern_proposals"

    cluster_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("document_clusters.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    anchor: Mapped[str | None] = mapped_column(String(500), nullable=True)
    strategy: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pattern_json: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON
    evidence_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    confidence_anchor: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_pattern: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_position: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_overall: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")

    cluster: Mapped[DocumentCluster] = relationship("DocumentCluster", back_populates="proposals")
