"""Tests for the extraction configuration schema validation."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.configuration import (
    AnchorConfig,
    ConfigurationSchema,
    ExtractionFieldSchema,
    ExtractionRuleSchema,
    ExtractionStrategy,
    OCRProfileSchema,
    PatternConfig,
    PatternType,
    RegionConfig,
    SearchConfig,
)


def test_valid_configuration_schema() -> None:
    """A fully valid configuration document should parse without errors."""
    config = ConfigurationSchema(
        id="invoice_config",
        name="Invoice Extraction",
        version=1,
        ocr_profile=OCRProfileSchema(provider="tesseract", language="eng", psm=6),
        fields=[
            ExtractionFieldSchema(
                id="invoice_number",
                metadata={"display_name": "Invoice Number"},
                output={"variable": "invoice_number", "type": "string"},
                extraction=ExtractionRuleSchema(
                    strategy=ExtractionStrategy.anchored_pattern,
                    anchor=AnchorConfig(value="Invoice No", minimum_similarity=0.9),
                    search=SearchConfig(),
                    pattern=PatternConfig(
                        type=PatternType.regex, value=r"INV-\d{4}-\d{5}"
                    ),
                ),
                normalization=["trim", "uppercase"],
                priority=100,
            )
        ],
    )
    assert config.id == "invoice_config"
    assert len(config.fields) == 1
    assert config.fields[0].id == "invoice_number"
    assert config.fields[0].extraction.anchor.value == "Invoice No"


def test_anchored_pattern_requires_anchor() -> None:
    """anchored_pattern strategy without an anchor must raise ValidationError."""
    with pytest.raises(ValidationError) as exc:
        ExtractionRuleSchema(
            strategy=ExtractionStrategy.anchored_pattern,
            anchor=None,
        )
    assert "anchored_pattern strategy requires an anchor configuration" in str(exc.value)


def test_region_strategy_requires_region() -> None:
    """region strategy without region config must raise ValidationError."""
    with pytest.raises(ValidationError) as exc:
        ExtractionRuleSchema(
            strategy=ExtractionStrategy.region,
            region=None,
        )
    assert "region strategy requires a region configuration" in str(exc.value)


def test_invalid_field_id_pattern() -> None:
    """Field IDs must be snake_case starting with a lowercase letter."""
    with pytest.raises(ValidationError):
        ExtractionFieldSchema(
            id="123invalid",
            extraction=ExtractionRuleSchema(
                strategy=ExtractionStrategy.direct_pattern,
                pattern=PatternConfig(type=PatternType.regex, value=r"\d+"),
            ),
        )


def test_region_config_validation() -> None:
    """Region coordinates must be between 0.0 and 1.0."""
    region = RegionConfig(x=0.1, y=0.2, width=0.5, height=0.3, page=1)
    assert region.x == 0.1

    with pytest.raises(ValidationError):
        RegionConfig(x=1.5, y=0.2, width=0.5, height=0.3, page=1)
