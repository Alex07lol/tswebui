"""Unit tests for the Output Type Inference service."""
from app.services.pattern.type_inferrer import infer_output_type


def test_infer_date_from_pattern_tokens():
    res = infer_output_type(human_pattern="{DD}/{MM}/{YYYY}")
    assert res.inferred_type == "date"
    assert res.confidence >= 0.90


def test_infer_currency_from_MONEY_token():
    res = infer_output_type(human_pattern="{MONEY}")
    assert res.inferred_type == "currency"
    assert res.confidence >= 0.90


def test_infer_number_from_pure_digit_pattern():
    res = infer_output_type(human_pattern="{NNNNNN}")
    assert res.inferred_type == "number"


def test_infer_text_from_mixed_pattern():
    res = infer_output_type(human_pattern="SN-{YYYY}-{NNNNNN}")
    assert res.inferred_type == "text"


def test_infer_from_date_examples():
    res = infer_output_type(examples=["2026-09-15", "2026-10-01"])
    assert res.inferred_type == "date"


def test_infer_from_currency_examples():
    res = infer_output_type(examples=["$1,250.00", "$99.50"])
    assert res.inferred_type == "currency"


def test_infer_boolean_from_name():
    res = infer_output_type(field_name="is_active")
    assert res.inferred_type == "boolean"
