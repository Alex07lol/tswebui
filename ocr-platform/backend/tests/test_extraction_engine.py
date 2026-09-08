"""Tests for Extraction Engine, Normalization, Validation, and End-to-End Extraction API."""
from __future__ import annotations

import io
import pytest
from httpx import AsyncClient
from PIL import Image, ImageDraw

from app.core.database import create_all_tables
from app.providers.ocr.base import BoundingBox, OCRPage, OCRResult, OCRWord
from app.schemas.configuration import (
    AnchorConfig,
    ConfigurationSchema,
    ExtractionFieldSchema,
    ExtractionRuleSchema,
    ExtractionStrategy,
    PatternConfig,
    PatternType,
    ValidationRules,
)
from app.services.extraction.anchors import AnchorMatcher
from app.services.extraction.confidence import ConfidenceEngine
from app.services.extraction.engine import ExtractionEngine
from app.services.extraction.patterns import PatternCompiler
from app.services.normalization.normalizer import Normalizer
from app.services.validation.validator import ValueValidator


def test_pattern_compiler_templates() -> None:
    """Template syntax translates into correct regex."""
    assert PatternCompiler.compile_template_to_regex("INV-{YYYY}-{NNNNN}") == r"INV-\d{4}-\d{5}"
    assert PatternCompiler.compile_template_to_regex("ORD-{YY}-{N}") == r"ORD-\d{2}-\d+"
    assert PatternCompiler.compile_template_to_regex("PO-{A}-{NN}") == r"PO-[A-Za-z]+-\d{2}"


def test_normalizer_steps() -> None:
    """Normalization pipeline applies steps sequentially."""
    raw = "  inv-2026-001  "
    steps = ["trim", "uppercase", {"replace": {"old": "-", "new": "_"}}]
    res = Normalizer.normalize(raw, steps)
    assert res == "INV_2026_001"


def test_value_validator() -> None:
    """Validator enforces presence, length, and regex."""
    rules = ValidationRules(required=True, min_length=5, regex=r"^INV-\d+$")
    ok, err = ValueValidator.validate("INV-12345", rules)
    assert ok is True
    assert err is None

    fail, err = ValueValidator.validate("INV", rules)
    assert fail is False
    assert "length" in str(err) or "pattern" in str(err)


def test_anchor_matcher_exact_and_fuzzy() -> None:
    """Anchor matcher finds exact and fuzzy occurrences on OCR page."""
    words = [
        OCRWord(text="Invoice", confidence=0.95, bounding_box=BoundingBox(10, 20, 50, 15), line_number=1, word_index=0),
        OCRWord(text="Number:", confidence=0.90, bounding_box=BoundingBox(65, 20, 60, 15), line_number=1, word_index=1),
        OCRWord(text="INV-9988", confidence=0.98, bounding_box=BoundingBox(130, 20, 70, 15), line_number=1, word_index=2),
    ]
    page = OCRPage(page_number=1, width=500, height=200, text="Invoice Number: INV-9988", words=words)

    # Exact match
    anchors = AnchorMatcher.find_anchors(page, AnchorConfig(value="Invoice Number:", match="exact"))
    assert len(anchors) == 1
    assert anchors[0].line_number == 1

    # Fuzzy match with slight typo
    fuzzy_anchors = AnchorMatcher.find_anchors(
        page, AnchorConfig(value="Invoce Numbr", match="fuzzy", minimum_similarity=0.75)
    )
    assert len(fuzzy_anchors) >= 1


def test_confidence_engine() -> None:
    """Confidence engine produces bounded, explainable scores."""
    breakdown = ConfidenceEngine.calculate(
        ocr_confidence=0.90,
        anchor_confidence=0.95,
        pattern_confidence=1.0,
        validation_passed=True,
    )
    assert 0.0 <= breakdown.overall <= 1.0
    assert breakdown.overall > 0.85
    assert breakdown.ocr == 0.90


@pytest.mark.anyio
async def test_end_to_end_extraction_api_flow(client: AsyncClient) -> None:
    """Full end-to-end API test: upload -> OCR -> create config -> test live -> publish -> run persistent job -> get evidence."""
    await create_all_tables()

    # 1. Create document with anchor and value
    img = Image.new("RGB", (500, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((15, 30), "Invoice Number: INV-2026-99999", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    upload_resp = await client.post(
        "/api/documents", files={"file": ("invoice_test.png", buf.getvalue(), "image/png")}
    )
    assert upload_resp.status_code == 201
    doc_id = upload_resp.json()["id"]

    # 2. Run OCR job
    ocr_resp = await client.post(
        "/api/ocr/jobs", json={"document_id": doc_id, "provider": "tesseract", "language": "eng", "psm": 6}
    )
    assert ocr_resp.status_code == 201

    # 3. Create extraction configuration
    cfg_payload = {
        "name": "Invoice Rules",
        "slug": "invoice_rules",
        "config": {
            "schema_version": 1,
            "id": "invoice_rules",
            "name": "Invoice Rules",
            "fields": [
                {
                    "id": "invoice_no",
                    "output": {"variable": "invoice_number", "type": "string"},
                    "extraction": {
                        "strategy": "anchored_pattern",
                        "anchor": {"value": "Invoice Number", "match": "fuzzy", "minimum_similarity": 0.6},
                        "search": {"direction": "after", "scope": "same_line"},
                        "pattern": {"type": "template", "value": "INV-{YYYY}-{NNNNN}"},
                    },
                    "normalization": ["trim", "uppercase"],
                    "validation": {"required": True},
                }
            ],
        },
    }
    create_cfg_resp = await client.post("/api/configurations", json=cfg_payload)
    assert create_cfg_resp.status_code == 201
    cfg_id = create_cfg_resp.json()["id"]

    # 4. Test live extraction without publishing
    live_resp = await client.post(
        "/api/configurations/test/live",
        json={"document_id": doc_id, "config": cfg_payload["config"]},
    )
    assert live_resp.status_code == 200
    live_data = live_resp.json()
    assert "invoice_number" in live_data["extracted_fields"]

    # 5. Publish configuration
    pub_resp = await client.post(f"/api/configurations/{cfg_id}/publish")
    assert pub_resp.status_code == 200
    assert pub_resp.json()["status"] == "active"

    # 6. Run persistent extraction job
    job_resp = await client.post(
        "/api/extraction/jobs", json={"document_id": doc_id, "config_id": cfg_id}
    )
    assert job_resp.status_code == 201
    job_data = job_resp.json()
    result_id = job_data["result_id"]
    assert "invoice_number" in job_data["fields"]

    # 7. Fetch persistent result by result_id
    res_resp = await client.get(f"/api/extraction/results/{result_id}")
    assert res_resp.status_code == 200
    res_data = res_resp.json()
    assert res_data["id"] == result_id
    assert "invoice_number" in res_data["fields"]
    assert res_data["fields"]["invoice_number"]["evidence"] is not None

    # Cleanup
    await client.delete(f"/api/documents/{doc_id}")
