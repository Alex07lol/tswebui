"""Unit tests for automatic field ID and output variable generation."""
from app.services.extraction.auto_strategy import _slugify, generate_auto_strategy


def test_display_name_to_field_id():
    assert _slugify("Serial Number") == "serial_number"
    assert _slugify("Purchase Date") == "purchase_date"


def test_display_name_with_special_chars():
    assert _slugify("Item # (Code)") == "item_code"
    assert _slugify("123 Field") == "field_123_field"


def test_output_variable_matches_field_id():
    res = generate_auto_strategy("Warranty Code", human_pattern="WC-{NNNN}")
    assert res.field_id == "warranty_code"
    assert res.output_type == "text"
