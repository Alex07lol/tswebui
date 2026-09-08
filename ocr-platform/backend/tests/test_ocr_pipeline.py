"""End-to-end integration tests for Document upload, Tesseract OCR, word bounding boxes, and caching."""
from __future__ import annotations

import io
import pytest
from httpx import AsyncClient
from PIL import Image, ImageDraw

from app.core.database import create_all_tables
from app.services.ocr.preprocessing import ImagePreprocessor


def create_test_image(text: str = "Invoice No: INV-2026-00128") -> bytes:
    """Generate a clean test image with text."""
    img = Image.new("RGB", (400, 80), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((15, 30), text, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.anyio
async def test_image_preprocessing_pipeline() -> None:
    """Preprocessing steps execute without errors on a PIL image."""
    img = Image.new("RGB", (100, 100), color=(200, 200, 200))
    profile = [
        "grayscale",
        "auto_contrast",
        {"contrast": {"factor": 1.5}},
        {"resize": {"scale": 1.5}},
        {"threshold": {"threshold": 128}},
    ]
    processed = ImagePreprocessor.process(img, profile)
    assert processed.size == (150, 150)
    assert processed.mode == "1" or processed.mode == "L"


@pytest.mark.anyio
async def test_document_upload_and_ocr_flow(client: AsyncClient) -> None:
    """Full lifecycle: Upload document -> Run OCR Job -> Retrieve OCR Words and BBoxes."""
    await create_all_tables()

    # 1. Upload document
    img_bytes = create_test_image("Total: 500.00")
    files = {"file": ("test_invoice.png", img_bytes, "image/png")}
    upload_resp = await client.post("/api/documents", files=files)
    assert upload_resp.status_code == 201
    doc_data = upload_resp.json()
    doc_id = doc_data["id"]
    assert doc_data["filename"] == "test_invoice.png"
    assert doc_data["page_count"] == 1
    assert doc_data["file_hash"] is not None

    # 2. Trigger OCR job
    job_payload = {
        "document_id": doc_id,
        "provider": "tesseract",
        "language": "eng",
        "psm": 6,
        "oem": 3,
    }
    job_resp = await client.post("/api/ocr/jobs", json=job_payload)
    assert job_resp.status_code == 201
    job_data = job_resp.json()
    assert job_data["status"] == "completed"

    # 3. Retrieve OCR results
    res_resp = await client.get(f"/api/ocr/results/{doc_id}")
    assert res_resp.status_code == 200
    res_data = res_resp.json()
    assert res_data["document_id"] == doc_id
    assert res_data["provider"] == "tesseract"
    assert len(res_data["pages"]) == 1
    page = res_data["pages"][0]
    assert page["page_number"] == 1
    assert len(page["words"]) > 0

    first_word = page["words"][0]
    assert first_word["text"] != ""
    assert first_word["confidence"] is not None
    assert first_word["bbox_x"] is not None
    assert first_word["bbox_width"] is not None

    # 4. Test caching: Second OCR job for same document hits cache
    cached_job_resp = await client.post("/api/ocr/jobs", json=job_payload)
    assert cached_job_resp.status_code == 201
    assert cached_job_resp.json()["status"] == "completed"

    # 5. Clean up document
    del_resp = await client.delete(f"/api/documents/{doc_id}")
    assert del_resp.status_code == 204
