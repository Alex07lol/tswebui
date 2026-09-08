"""Tests for extraction results retrieval and export formats (JSON, CSV, batch)."""
from __future__ import annotations

import io
import pytest
from PIL import Image, ImageDraw
from httpx import AsyncClient

from app.core.database import create_all_tables


def create_export_test_image() -> bytes:
    """Generate sample invoice image."""
    img = Image.new("RGB", (600, 200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((20, 30), "Invoice Number: INV-9901", fill=(0, 0, 0))
    d.text((20, 80), "Total: $1250.00", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.anyio
async def test_extraction_results_and_export_flow(client: AsyncClient) -> None:
    """Test full extraction result generation, retrieval, and CSV/JSON export."""
    await create_all_tables()

    # 1. Create configuration
    config_payload = {
        "name": "Export Test Config",
        "fields": [
            {
                "field_id": "inv_num",
                "display_name": "Invoice Number",
                "output_variable": "invoice_number",
                "rules": [
                    {
                        "strategy": "anchored_pattern",
                        "anchor": {"value": "Invoice Number", "match": "fuzzy"},
                        "pattern": {"type": "regex", "value": r"INV-\d+"},
                        "search": {"direction": "after", "scope": "same_line"},
                    }
                ],
            },
            {
                "field_id": "total",
                "display_name": "Total",
                "output_variable": "total_amount",
                "rules": [
                    {
                        "strategy": "anchored_pattern",
                        "anchor": {"value": "Total", "match": "fuzzy"},
                        "pattern": {"type": "regex", "value": r"\d+\.\d{2}"},
                        "search": {"direction": "after", "scope": "same_line"},
                    }
                ],
            },
        ],
    }
    cfg_resp = await client.post("/api/configurations", json=config_payload)
    assert cfg_resp.status_code == 201
    cfg_data = cfg_resp.json()
    version_id = cfg_data["versions"][0]["id"]

    # 2. Upload document and run OCR
    img_bytes = create_export_test_image()
    upload_resp = await client.post(
        "/api/documents", files={"file": ("export_invoice.png", img_bytes, "image/png")}
    )
    assert upload_resp.status_code == 201
    doc_id = upload_resp.json()["id"]

    await client.post(
        "/api/ocr/jobs",
        json={"document_id": doc_id, "provider": "tesseract", "language": "eng"},
    )

    # 3. Trigger extraction job
    job_resp = await client.post(
        "/api/extraction/jobs",
        json={"document_id": doc_id, "config_version_id": version_id},
    )
    assert job_resp.status_code == 201
    job_id = job_resp.json()["id"]

    # 4. Retrieve result by document_id
    doc_res_resp = await client.get(f"/api/results/document/{doc_id}")
    assert doc_res_resp.status_code == 200
    res_data = doc_res_resp.json()
    res_id = res_data["result_id"]
    assert res_data["document_id"] == doc_id
    assert "invoice_number" in res_data["extracted_data"]
    assert "total_amount" in res_data["extracted_data"]

    # 5. Export single result as JSON
    json_export = await client.get(f"/api/results/{res_id}/export?format=json")
    assert json_export.status_code == 200
    assert json_export.headers["content-type"].startswith("application/json")
    exported_json = json_export.json()
    assert exported_json["result_id"] == res_id
    assert "extracted_data" in exported_json

    # 6. Export single result as CSV
    csv_export = await client.get(f"/api/results/{res_id}/export?format=csv")
    assert csv_export.status_code == 200
    assert "text/csv" in csv_export.headers["content-type"]
    csv_lines = csv_export.text.strip().split("\r\n" if "\r\n" in csv_export.text else "\n")
    assert len(csv_lines) >= 2  # Header + 1 row
    assert "invoice_number" in csv_lines[0]
    assert "total_amount" in csv_lines[0]

    # 7. Batch export as CSV
    batch_resp = await client.post(
        "/api/results/batch-export",
        json={"result_ids": [res_id], "format": "csv"},
    )
    assert batch_resp.status_code == 200
    assert "text/csv" in batch_resp.headers["content-type"]
