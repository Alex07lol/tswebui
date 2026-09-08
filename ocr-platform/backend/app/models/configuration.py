"""Configuration, version, field, and rule models."""
from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Configuration(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A named extraction configuration that can own multiple versions."""

    __tablename__ = "configurations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    versions: Mapped[list[ConfigurationVersion]] = relationship(
        "ConfigurationVersion", back_populates="configuration", cascade="all, delete-orphan"
    )


class ConfigurationVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A specific version snapshot of an extraction configuration.

    Lifecycle: draft → tested → review → published → active → deprecated
    """

    __tablename__ = "configuration_versions"

    configuration_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("configurations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # Full YAML/JSON config snapshot stored for exact replay
    config_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_profile: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    change_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    configuration: Mapped[Configuration] = relationship(
        "Configuration", back_populates="versions"
    )
    fields: Mapped[list[ExtractionField]] = relationship(
        "ExtractionField", back_populates="version", cascade="all, delete-orphan"
    )


class ExtractionField(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A single named field to be extracted by a configuration version."""

    __tablename__ = "extraction_fields"

    version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("configuration_versions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    field_id: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. invoice_number
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_variable: Mapped[str] = mapped_column(String(100), nullable=False)
    output_type: Mapped[str] = mapped_column(String(50), nullable=False, default="string")
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    normalization_steps: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    validation_rules: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    version: Mapped[ConfigurationVersion] = relationship(
        "ConfigurationVersion", back_populates="fields"
    )
    rules: Mapped[list[ExtractionRule]] = relationship(
        "ExtractionRule", back_populates="field", cascade="all, delete-orphan"
    )


class ExtractionRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Defines how to locate and extract a field value from OCR output."""

    __tablename__ = "extraction_rules"

    field_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("extraction_fields.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    rule_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # anchored_pattern | direct_pattern | same_line | next_line | multi_line | region | relative
    strategy: Mapped[str] = mapped_column(String(100), nullable=False)
    anchor_config: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON
    search_config: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON
    pattern_config: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    region_config: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    field: Mapped[ExtractionField] = relationship("ExtractionField", back_populates="rules")
