"""Tests for Dataset management, Clustering, Pattern Learning, and Proposal Promotion API."""
from __future__ import annotations

import io
import pytest
from httpx import AsyncClient
from PIL import Image, ImageDraw

from app.core.database import create_all_tables


def create_sample_invoice(doc_num: str, amount: str) -> bytes:
    """Create a sample invoice image with stable anchor and variable value."""
    img = Image.new("RGB", (500, 120), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((15, 25), "Company Acme Corp", fill=(0, 0, 0))
    draw.text((15, 55), f"Total Due: {amount}", fill=(0, 0, 0))
    draw.text((15, 85), f"Invoice Number: INV-{doc_num}", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.anyio
async def test_dataset_pattern_learning_pipeline(client: AsyncClient) -> None:
    """Test full pattern discovery flow from raw documents to approved configuration."""
    await create_all_tables()

    # 1. Upload two sample documents sharing structure
    doc_ids: list[str] = []
    for num, amt in [("1001", "$450.00"), ("1002", "$920.00")]:
        img_bytes = create_sample_invoice(num, amt)
        files = {"file": (f"sample_inv_{num}.png", img_bytes, "image/png")}
        up_resp = await client.post("/api/documents", files=files)
        assert up_resp.status_code == 201
        doc_id = up_resp.json()["id"]
        doc_ids.append(doc_id)

        # Run OCR
        ocr_resp = await client.post(
            "/api/ocr/jobs",
            json={"document_id": doc_id, "provider": "tesseract", "language": "eng", "psm": 6},
        )
        assert ocr_resp.status_code == 201

    # 2. Create Dataset
    ds_resp = await client.post(
        "/api/datasets", json={"name": "Invoice Learning Set", "description": "Sample invoices"}
    )
    assert ds_resp.status_code == 201
    dataset_id = ds_resp.json()["id"]

    # 3. Add documents to Dataset
    add_resp = await client.post(
        f"/api/datasets/{dataset_id}/documents",
        json={"document_ids": doc_ids},
    )
    assert add_resp.status_code == 200
    assert add_resp.json()["total_documents"] == 2

    # 4. Trigger Discovery
    disc_resp = await client.post(f"/api/datasets/{dataset_id}/discover")
    assert disc_resp.status_code == 201
    disc_data = disc_resp.json()
    run_id = disc_data["run_id"]
    assert disc_data["status"] == "completed"
    assert disc_data["documents_processed"] == 2
    assert disc_data["clusters_found"] >= 1
    assert disc_data["proposals_generated"] >= 1

    # 5. Fetch Discovery Run & Proposals
    run_resp = await client.get(f"/api/discovery/runs/{run_id}")
    assert run_resp.status_code == 200
    assert len(run_resp.json()["clusters"]) >= 1

    prop_resp = await client.get(f"/api/discovery/runs/{run_id}/proposals")
    assert prop_resp.status_code == 200
    proposals = prop_resp.json()
    assert len(proposals) >= 1

    first_prop = proposals[0]
    prop_id = first_prop["id"]
    assert first_prop["anchor"] != ""
    assert first_prop["confidence"]["overall"] > 0.5
    assert first_prop["status"] == "pending"

    # 6. Approve proposal -> promotes to ExtractionConfiguration
    approve_resp = await client.post(
        f"/api/proposals/{prop_id}/approve",
        json={"configuration_name": "Auto-Learned Invoice Config"},
    )
    assert approve_resp.status_code == 200
    appr_data = approve_resp.json()
    assert appr_data["status"] == "approved"
    target_cfg_id = appr_data["configuration_id"]
    assert target_cfg_id is not None

    # 7. Check the generated configuration
    cfg_resp = await client.get(f"/api/configurations/{target_cfg_id}")
    assert cfg_resp.status_code == 200
    cfg_data = cfg_resp.json()
    assert len(cfg_data["config"]["fields"]) >= 1

    # Clean up
    for did in doc_ids:
        await client.delete(f"/api/documents/{did}")
