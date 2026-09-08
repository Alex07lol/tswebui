"""Pydantic schemas for extraction configuration.

These schemas validate the declarative YAML/JSON configuration that drives
extraction. They are the single source of truth for what a valid configuration
looks like. The ORM models store these as JSON snapshots for versioning.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class AnchorMatchMode(str, Enum):
    exact = "exact"
    fuzzy = "fuzzy"
    regex = "regex"


class SearchDirection(str, Enum):
    after = "after"
    before = "before"
    left = "left"
    right = "right"


class SearchScope(str, Enum):
    same_line = "same_line"
    next_line = "next_line"
    multi_line = "multi_line"
    region = "region"
    document = "document"


class ExtractionStrategy(str, Enum):
    anchored_pattern = "anchored_pattern"
    direct_pattern = "direct_pattern"
    same_line = "same_line"
    next_line = "next_line"
    multi_line = "multi_line"
    region = "region"
    relative = "relative"
    table = "table"


class PatternType(str, Enum):
    regex = "regex"
    template = "template"
    typed = "typed"
    example = "example"


class OutputType(str, Enum):
    string = "string"
    integer = "integer"
    decimal = "decimal"
    date = "date"
    currency = "currency"
    boolean = "boolean"


class AnchorConfig(BaseModel):
    """Configures how an anchor label is located in the OCR output."""

    value: str = Field(..., description="The anchor text to search for")
    match: AnchorMatchMode = AnchorMatchMode.fuzzy
    minimum_similarity: float = Field(0.85, ge=0.0, le=1.0)


class SearchConfig(BaseModel):
    """Configures where to search relative to the anchor."""

    direction: SearchDirection = SearchDirection.after
    scope: SearchScope = SearchScope.same_line
    max_lines: int = Field(5, ge=1, le=50)
    max_distance_px: int | None = None


class PatternConfig(BaseModel):
    """Configures the pattern used to identify the target value."""

    type: PatternType = PatternType.regex
    value: str | None = None
    examples: list[str] = Field(default_factory=list)
    named_type: str | None = None


class RegionConfig(BaseModel):
    """Configures a page region for region-based extraction."""

    x: float = Field(..., ge=0.0, le=1.0)
    y: float = Field(..., ge=0.0, le=1.0)
    width: float = Field(..., ge=0.0, le=1.0)
    height: float = Field(..., ge=0.0, le=1.0)
    page: int = Field(1, ge=1)


class ValidationRules(BaseModel):
    """Validation constraints applied to a normalized value."""

    required: bool = False
    regex: str | None = None
    min_length: int | None = None
    max_length: int | None = None
    min_value: float | None = None
    max_value: float | None = None
    allowed_values: list[str] = Field(default_factory=list)


class ExtractionRuleSchema(BaseModel):
    """Declarative rule describing how to extract a single field value."""

    strategy: ExtractionStrategy
    anchor: AnchorConfig | None = None
    search: SearchConfig = Field(default_factory=SearchConfig)
    pattern: PatternConfig | None = None
    region: RegionConfig | None = None
    priority: int = 100

    @model_validator(mode="after")
    def validate_strategy_requirements(self) -> "ExtractionRuleSchema":
        """Ensure required sub-configs are present for each strategy."""
        if self.strategy == ExtractionStrategy.anchored_pattern and self.anchor is None:
            raise ValueError("anchored_pattern strategy requires an anchor configuration")
        if self.strategy == ExtractionStrategy.region and self.region is None:
            raise ValueError("region strategy requires a region configuration")
        return self


class ExtractionFieldSchema(BaseModel):
    """Schema for a single named extraction field."""

    id: str = Field(..., pattern=r"^[a-z][a-z0-9_]*$")
    metadata: dict[str, str] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    extraction: ExtractionRuleSchema
    normalization: list[str] = Field(default_factory=list)
    validation: ValidationRules = Field(default_factory=ValidationRules)
    priority: int = 100


class OCRProfileSchema(BaseModel):
    """OCR provider and language settings."""

    provider: str = "tesseract"
    language: str = "eng"
    psm: int = Field(6, ge=0, le=13)
    oem: int = Field(3, ge=0, le=3)
    preprocessing_profile: str | None = None


class ConfigurationSchema(BaseModel):
    """Root schema for a complete extraction configuration document."""

    schema_version: int = 1
    id: str = Field(..., pattern=r"^[a-z][a-z0-9_]*$")
    name: str
    version: int = 1
    ocr_profile: OCRProfileSchema = Field(default_factory=OCRProfileSchema)
    fields: list[ExtractionFieldSchema] = Field(default_factory=list)
