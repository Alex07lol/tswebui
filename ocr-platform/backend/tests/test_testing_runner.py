"""Tests for test runner, regression testing, and suite execution."""
from __future__ import annotations

import io
import pytest
from PIL import Image, ImageDraw
from httpx import AsyncClient

from app.core.database import create_all_tables
from app.core.database import AsyncSessionLocal
from app.services.ocr.service import OCRService
from app.services.extraction.engine import ExtractionEngine


def create_invoice_image() -> bytes:
    """Generate image containing invoice text."""
    img = Image.new("RGB", (600, 200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((20, 50), "Invoice Number: INV-2026-00100", fill=(0, 0, 0))
    scaled = img.resize((1800, 600), Image.Resampling.NEAREST)
    buf = io.BytesIO()
    scaled.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.anyio
async def test_test_suite_and_regression_runner_flow(client: AsyncClient) -> None:
    """Test creating test suite, test cases, running tests, and verifying diffs."""
    await create_all_tables()

    # 1. Create a configuration and a published version
    config_payload = {
        "name": "Invoice Suite Config",
        "description": "Config for testing runner",
        "fields": [
            {
                "field_id": "inv_num",
                "display_name": "Invoice Number",
                "output_variable": "invoice_number",
                "output_type": "string",
                "required": True,
                "rules": [
                    {
                        "strategy": "anchored_pattern",
                        "anchor": {"value": "Invoice Number", "match": "fuzzy", "minimum_similarity": 0.6},
                        "pattern": {"type": "regex", "value": r"[A-Za-z0-9]+-\d{4}-\d{5}"},
                        "search": {"direction": "after", "scope": "same_line"},
                    }
                ],
            }
        ],
    }
    cfg_resp = await client.post("/api/configurations", json=config_payload)
    assert cfg_resp.status_code == 201
    cfg_id = cfg_resp.json()["id"]

    # 2. Upload test document and perform OCR
    img_bytes = create_invoice_image()
    upload_resp = await client.post(
        "/api/documents", files={"file": ("invoice_test.png", img_bytes, "image/png")}
    )
    assert upload_resp.status_code == 201
    doc_id = upload_resp.json()["id"]

    ocr_resp = await client.post(
        "/api/ocr/jobs",
        json={"document_id": doc_id, "provider": "tesseract", "language": "eng"},
    )
    assert ocr_resp.status_code == 201

    # Fetch OCR result to get exact extracted value for exact match test
    async with AsyncSessionLocal() as session:
        ocr_res = await OCRService().get_ocr_result_for_document(session, doc_id)
        assert ocr_res is not None
        extracted = ExtractionEngine.extract_document(ocr_res, config_payload["fields"])
        actual_val = extracted["invoice_number"].raw_value
        assert actual_val is not None

    # 3. Create a TestSuite for this configuration
    suite_payload = {
        "configuration_id": cfg_id,
        "name": "Regression Test Suite",
        "description": "Automated regression tests",
    }
    suite_resp = await client.post("/api/tests/suites", json=suite_payload)
    assert suite_resp.status_code == 201
    suite_id = suite_resp.json()["id"]

    # 4. Add TestCase 1: Passing case with exact match
    case1_payload = {
        "document_id": doc_id,
        "name": "Invoice Exact Value Test",
        "expected_values": {"invoice_number": actual_val},
        "validation_mode": "exact",
        "is_regression": True,
    }
    case1_resp = await client.post(f"/api/tests/suites/{suite_id}/cases", json=case1_payload)
    assert case1_resp.status_code == 201
    assert case1_resp.json()["is_regression"] is True

    # 5. Add TestCase 2: Regex match mode
    case2_payload = {
        "document_id": doc_id,
        "name": "Invoice Regex Pattern Test",
        "expected_values": {"invoice_number": r".*-\d{4}-\d{5}"},
        "validation_mode": "regex",
        "is_regression": False,
    }
    case2_resp = await client.post(f"/api/tests/suites/{suite_id}/cases", json=case2_payload)
    assert case2_resp.status_code == 201

    # 6. Run the TestSuite
    run_resp = await client.post(f"/api/tests/suites/{suite_id}/run", json={})
    assert run_resp.status_code == 200, run_resp.text
    run_data = run_resp.json()
    assert run_data["status"] == "passed"
    assert run_data["total_cases"] == 2
    assert run_data["passed_cases"] == 2
    assert run_data["failed_cases"] == 0
    assert run_data["pass_rate"] == 1.0
    assert len(run_data["results"]) == 2
    assert run_data["results"][0]["passed"] is True
    assert run_data["results"][1]["passed"] is True

    # 7. List test runs for the suite
    runs_resp = await client.get(f"/api/tests/suites/{suite_id}/runs")
    assert runs_resp.status_code == 200
    assert len(runs_resp.json()) == 1
