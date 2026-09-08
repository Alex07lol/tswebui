"""Test suite, test case, and test run models."""
from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class TestSuite(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A named collection of test cases owned by a configuration."""

    __tablename__ = "test_suites"

    configuration_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("configurations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class TestCase(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A single test: one document + expected extraction values."""

    __tablename__ = "test_cases"

    suite_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("test_suites.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    document_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    expected_values_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    # exact | regex | numeric_tolerance | date_equivalent | required_presence
    validation_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="exact")
    is_regression: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class TestRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Records the outcome of running a test suite against a configuration version."""

    __tablename__ = "test_runs"

    suite_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("test_suites.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    config_version_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("configuration_versions.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    total_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    passed_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pass_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    results_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
