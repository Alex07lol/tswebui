"""Universal Data Layer models for TSWebUI.

Provides domain-agnostic data modeling, schema definition, typed records,
cross-record relationships, and explicit website membership.
"""
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class DataSource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Represents a structured data source (OCR setups, manual datasets, external imports)."""

    __tablename__ = "data_sources"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="ocr_records"
    )  # ocr_records | manual | imported | computed | external_api
    setup_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("configurations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active"
    )  # active | draft | archived
    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    schemas: Mapped[list[DataSchema]] = relationship(
        "DataSchema", back_populates="data_source", cascade="all, delete-orphan"
    )
    records: Mapped[list[DataRecord]] = relationship(
        "DataRecord", back_populates="data_source", cascade="all, delete-orphan"
    )
    website_links: Mapped[list[WebsiteDataSource]] = relationship(
        "WebsiteDataSource", back_populates="data_source", cascade="all, delete-orphan"
    )


class DataSchema(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Schema version definition for a DataSource containing typed DataFields."""

    __tablename__ = "data_schemas"

    data_source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="Default Schema")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    fields_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    data_source: Mapped[DataSource] = relationship("DataSource", back_populates="schemas")
    fields: Mapped[list[DataField]] = relationship(
        "DataField", back_populates="schema", cascade="all, delete-orphan"
    )


class DataField(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A typed field definition in a DataSchema."""

    __tablename__ = "data_fields"

    schema_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("data_schemas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="string"
    )  # string | long_text | integer | decimal | boolean | date | datetime | email | url | file | image | document | json
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    searchable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sortable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    filterable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    displayable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    public_readable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    semantic_role: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # title | identifier | badge | metadata | status | date | numeric | image | document
    validation_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    schema: Mapped[DataSchema] = relationship("DataSchema", back_populates="fields")


class DataRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """An individual structured record within a DataSource (backed by OCR or manual input)."""

    __tablename__ = "data_records"

    data_source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_document_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    values_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active"
    )  # active | archived | draft

    data_source: Mapped[DataSource] = relationship("DataSource", back_populates="records")


class DataRelation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Cross-record relational link between records."""

    __tablename__ = "data_relations"

    source_record_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("data_records.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_field_key: Mapped[str] = mapped_column(String(100), nullable=False)
    target_record_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("data_records.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_field_key: Mapped[str] = mapped_column(String(100), nullable=False)
    relation_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="reference"
    )  # reference | one_to_one | one_to_many | parent_child


class WebsiteDataSource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Links a Website to one or more DataSources."""

    __tablename__ = "website_data_sources"

    website_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    data_source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alias: Mapped[str | None] = mapped_column(String(100), nullable=True)
    default_source: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    data_source: Mapped[DataSource] = relationship("DataSource", back_populates="website_links")


class WebsiteDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Explicit membership linking a Document to a Website with public visibility gating."""

    __tablename__ = "website_documents"

    website_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_included: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
