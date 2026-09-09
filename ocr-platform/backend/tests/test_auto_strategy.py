"""Unit tests for automatic extraction strategy generation."""
from app.services.extraction.auto_strategy import generate_auto_strategy


def test_single_match_uses_anchored_or_direct():
    text = "Product Details\nSerial Number: SN-2026-004821\nOther text here"
    res = generate_auto_strategy(
        display_name="Serial Number",
        human_pattern="SN-{YYYY}-{NNNNNN}",
        ocr_text=text,
    )
    assert res.strategy == "anchored_pattern"
    assert res.confidence >= 0.90
    assert len(res.candidates) == 1
    assert res.candidates[0].value == "SN-2026-004821"


def test_direct_pattern_when_no_label():
    text = "Random words SN-2026-004821 floating without label"
    res = generate_auto_strategy(
        display_name="Device Code",
        human_pattern="SN-{YYYY}-{NNNNNN}",
        ocr_text=text,
    )
    assert res.strategy == "direct_pattern"
    assert len(res.candidates) == 1


def test_multiple_matches_triggers_ambiguous_if_unlabeled():
    text = "Items: SN-2026-001234 and SN-2026-001235 found here"
    res = generate_auto_strategy(
        display_name="Device Code",
        human_pattern="SN-{YYYY}-{NNNNNN}",
        ocr_text=text,
    )
    assert len(res.candidates) == 2
    assert res.ambiguous is True


def test_rule_dict_conforms_to_schema():
    res = generate_auto_strategy(
        display_name="Invoice Number",
        human_pattern="INV-{NNNNN}",
    )
    assert "strategy" in res.rule_dict
    assert "pattern" in res.rule_dict
    assert res.rule_dict["priority"] == 100
