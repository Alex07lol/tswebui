"""Phase 8 — Advanced Intelligence test suite."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.learning.corrections import (
    Correction,
    CorrectionEngine,
    _infer_pattern,
)
from app.services.intelligence.suggestions import suggest_fields
from app.services.ocr.training import evaluate_ocr
from app.providers.ocr.mock_vision import MockVisionProvider


# ─── Unit: CorrectionEngine ───────────────────────────────────────────────────

def test_correction_engine_records_history() -> None:
    engine = CorrectionEngine()
    correction = Correction(
        document_id="doc-1",
        field_name="total_amount",
        original_value="$100",
        corrected_value="$1,234.56",
        ocr_tokens=["Total", ":", "$1,234.56"],
    )
    insight = engine.record(correction)
    assert insight.field_name == "total_amount"
    assert insight.confidence_delta == pytest.approx(0.05)
    assert engine.history_count("total_amount") == 1


def test_correction_engine_accumulates_delta() -> None:
    engine = CorrectionEngine()
    for i in range(5):
        engine.record(
            Correction(
                document_id=f"doc-{i}",
                field_name="invoice_number",
                original_value=None,
                corrected_value=f"INV-{i:04d}",
            )
        )
    insight = engine.get_insights("invoice_number")
    assert insight is not None
    assert insight.confidence_delta == pytest.approx(0.25)


def test_correction_engine_unknown_field_returns_none() -> None:
    engine = CorrectionEngine()
    assert engine.get_insights("nonexistent_field") is None


def test_correction_engine_all_field_names() -> None:
    engine = CorrectionEngine()
    engine.record(Correction("d1", "field_a", None, "val1"))
    engine.record(Correction("d2", "field_b", None, "val2"))
    names = engine.all_field_names()
    assert "field_a" in names
    assert "field_b" in names


def test_infer_pattern_currency() -> None:
    values = ["$1,234.56", "$99.00", "$0.50"]
    pattern = _infer_pattern(values)
    assert pattern is not None
    assert "\\d" in pattern


def test_infer_pattern_date() -> None:
    values = ["01/15/2024", "12/31/2023", "06/01/2024"]
    pattern = _infer_pattern(values)
    assert pattern is not None


def test_infer_pattern_empty_returns_none() -> None:
    assert _infer_pattern([]) is None


# ─── Unit: Suggestion Engine ──────────────────────────────────────────────────

INVOICE_TEXT = """
INVOICE #INV-2024-001
Bill To: Acme Corp
Invoice Date: 01/15/2024
Due Date: 02/15/2024

Subtotal: $1,000.00
Tax: $234.56
Total Due: $1,234.56

Tax ID: 12-3456789
"""


def test_suggest_fields_invoice_text() -> None:
    suggestions = suggest_fields(INVOICE_TEXT, top_k=10)
    field_names = [s.field_name for s in suggestions]
    assert len(suggestions) > 0
    # invoice text should trigger at least these
    assert any(f in field_names for f in ["invoice_number", "invoice_date", "total_amount"])


def test_suggest_fields_returns_sorted_by_confidence() -> None:
    suggestions = suggest_fields(INVOICE_TEXT)
    confidences = [s.confidence for s in suggestions]
    assert confidences == sorted(confidences, reverse=True)


def test_suggest_fields_empty_text_returns_empty() -> None:
    # all lowercase, no dates/amounts/uppercase — nothing to match
    suggestions = suggest_fields("the quick brown fox jumps over the lazy dog")
    assert suggestions == []


def test_suggest_fields_respects_top_k() -> None:
    suggestions = suggest_fields(INVOICE_TEXT, top_k=2)
    assert len(suggestions) <= 2


# ─── Unit: OCR Training Metrics ───────────────────────────────────────────────

def test_evaluate_ocr_identical_strings() -> None:
    metrics = evaluate_ocr("hello world", "hello world")
    assert metrics.cer == 0.0
    assert metrics.wer == 0.0


def test_evaluate_ocr_different_strings() -> None:
    metrics = evaluate_ocr("helo world", "hello world")
    assert metrics.cer > 0.0
    assert metrics.edits >= 1


def test_evaluate_ocr_word_error_rate() -> None:
    metrics = evaluate_ocr("foo bar baz", "foo bar quux")
    assert metrics.wer > 0.0


def test_evaluate_ocr_char_count() -> None:
    gt = "hello world"
    metrics = evaluate_ocr("hello world", gt)
    assert metrics.char_count == len(gt)


# ─── Unit: MockVisionProvider ─────────────────────────────────────────────────

def test_mock_vision_is_available() -> None:
    provider = MockVisionProvider()
    assert provider.is_available() is True


@pytest.mark.asyncio
async def test_mock_vision_process_image(tmp_path: object) -> None:
    import pathlib
    from app.providers.ocr.base import OCROptions
    provider = MockVisionProvider()
    fake_image = pathlib.Path(str(tmp_path)) / "test_invoice.png"
    fake_image.touch()
    opts = OCROptions()
    result = provider.process("doc-mock-1", str(fake_image), opts)
    assert result.provider == "mock_vision"
    assert len(result.pages) > 0
    assert result.full_text


# ─── Integration: API endpoints ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_api_submit_correction() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/corrections",
            json={
                "document_id": "doc-test-1",
                "field_name": "invoice_total",
                "original_value": "$100",
                "corrected_value": "$1,234.56",
                "ocr_tokens": ["Total", ":", "$1,234.56"],
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["field_name"] == "invoice_total"
    assert "confidence_delta" in data


@pytest.mark.asyncio
async def test_api_get_field_insight() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # first record a correction
        await client.post(
            "/api/corrections",
            json={
                "document_id": "doc-2",
                "field_name": "vendor_name",
                "original_value": None,
                "corrected_value": "Acme Corp",
                "ocr_tokens": [],
            },
        )
        resp = await client.get("/api/corrections/vendor_name/insight")
    assert resp.status_code == 200
    data = resp.json()
    assert data["field_name"] == "vendor_name"
    assert data["correction_count"] >= 1


@pytest.mark.asyncio
async def test_api_list_learned_fields() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/corrections/fields")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_api_suggest_rules() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/intelligence/suggest-rules",
            json={"ocr_text": INVOICE_TEXT, "top_k": 5},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] > 0
    assert len(data["suggestions"]) <= 5
    assert all("field_name" in s for s in data["suggestions"])
    assert all("confidence" in s for s in data["suggestions"])


@pytest.mark.asyncio
async def test_api_training_evaluate() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/training/evaluate",
            json={"predicted_text": "hello world", "ground_truth_text": "hello world"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["cer"] == 0.0
    assert data["wer"] == 0.0
    assert data["cer_percent"] == 0.0
