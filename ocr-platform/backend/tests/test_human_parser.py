"""Unit tests for the Human Pattern Language parser."""
import re
from app.services.pattern.human_parser import (
    compile_human_pattern,
    infer_from_description,
    infer_from_examples,
)


def test_parse_YYYY_token():
    res = compile_human_pattern("{YYYY}")
    assert res.regex == r"\d{4}"
    assert res.tokens == ["{YYYY}"]
    assert re.match(r"^\d{4}$", "2026")


def test_parse_NNNNNN_token():
    res = compile_human_pattern("{NNNNNN}")
    assert res.regex == r"\d{6}"
    assert re.match(res.regex, "001234")


def test_parse_MONEY_token():
    res = compile_human_pattern("{MONEY}")
    assert re.search(res.regex, "$1,250.00")
    assert re.search(res.regex, "99.95")


def test_parse_EMAIL_token():
    res = compile_human_pattern("{EMAIL}")
    assert re.search(res.regex, "contact@example.com")


def test_parse_composite_pattern_SN_YYYY_NNNNNN():
    res = compile_human_pattern("SN-{YYYY}-{NNNNNN}")
    assert r"\d{4}" in res.regex
    assert r"\d{6}" in res.regex
    assert re.match(res.regex, "SN-2026-001234")


def test_compile_matches_example():
    res = compile_human_pattern("INV-{YYYY}-{NNNN}")
    assert re.match(res.regex, "INV-2024-9988")


def test_infer_from_examples_serial():
    examples = ["SN-2026-001234", "SN-2026-001235", "SN-2026-001236"]
    res = infer_from_examples(examples)
    assert "{YYYY}" in res.inferred_human_pattern
    assert "{NNNNNN}" in res.inferred_human_pattern
    assert res.confidence >= 0.85


def test_infer_from_examples_date():
    examples = ["15/09/2026", "20/10/2026"]
    res = infer_from_examples(examples)
    assert res.inferred_human_pattern == "{DD}/{MM}/{YYYY}"


def test_plain_language_year_and_six_numbers():
    res = infer_from_description("Starts with SN, followed by the year, then six numbers")
    assert "SN" in res.inferred_human_pattern
    assert "{YYYY}" in res.inferred_human_pattern
    assert "{NNNNNN}" in res.inferred_human_pattern


def test_plain_language_date():
    res = infer_from_description("Contains day, month, and year separated by slash")
    assert "{DD}" in res.inferred_human_pattern
    assert "{MM}" in res.inferred_human_pattern
    assert "{YYYY}" in res.inferred_human_pattern
