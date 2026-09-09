"""Comprehensive regression and verification tests for TSWebUI Universal Website & Application Builder.

Covers:
1. Admin Authentication & RBAC Enforcement (401 on missing auth, 403 on insufficient role, 200 on admin)
2. Public Site Isolation & Zero Draft Leaks
3. Published Version Immutability & Draft Branching (editing published site never mutates live snapshot)
4. Explicit Document Membership Gating (Rule G & H: publishing only exposes explicit public members)
5. Universal Data Layer & Multi-Domain Scenarios (drawings, warranties, certificates, dashboards)
6. Visual PDF Locator with On-The-Fly Field Creation
"""
from __future__ import annotations

import json
import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import create_all_tables
from app.main import create_app
from app.models.data import DataSource, DataRecord, WebsiteDocument
from app.models.document import Document
from app.models.website import Website, WebsiteVersion


@pytest.fixture(autouse=True)
async def setup_db():
    await create_all_tables()


@pytest.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def admin_auth(client: AsyncClient) -> dict[str, str]:
    email = f"admin_{uuid.uuid4().hex[:6]}@example.com"
    await client.post("/api/auth/register", json={
        "email": email,
        "password": "password123",
        "role": "admin",
    })
    res = await client.post("/api/auth/login", json={
        "email": email,
        "password": "password123",
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def viewer_auth(client: AsyncClient) -> dict[str, str]:
    email = f"viewer_{uuid.uuid4().hex[:6]}@example.com"
    await client.post("/api/auth/register", json={
        "email": email,
        "password": "password123",
        "role": "viewer",
    })
    res = await client.post("/api/auth/login", json={
        "email": email,
        "password": "password123",
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_admin_auth_and_rbac_enforcement(client: AsyncClient, admin_auth: dict[str, str], viewer_auth: dict[str, str]):
    """Verify that admin endpoints strictly enforce authentication and reject viewers with 403."""
    payload = {
        "name": "Secret Internal Portal",
    }

    # 1. Unauthenticated request -> 401 Unauthorized
    no_auth_res = await client.post("/api/admin/websites", json=payload)
    assert no_auth_res.status_code == 401, no_auth_res.text
    assert "Authentication required" in no_auth_res.json()["detail"]

    # 2. Viewer role request -> 403 Forbidden
    viewer_res = await client.post("/api/admin/websites", json=payload, headers=viewer_auth)
    assert viewer_res.status_code == 403, viewer_res.text
    assert "Access forbidden" in viewer_res.json()["detail"]

    # 3. Admin role request -> 200 OK
    admin_res = await client.post("/api/admin/websites", json=payload, headers=admin_auth)
    assert admin_res.status_code == 200, admin_res.text
    assert admin_res.json()["name"] == "Secret Internal Portal"


@pytest.mark.asyncio
async def test_public_isolation_and_no_draft_fallback(client: AsyncClient, admin_auth: dict[str, str]):
    """Verify that a site in draft status is never exposed to public consumers (Rule D)."""
    # Create draft website
    res = await client.post("/api/admin/websites", json={
        "name": "Draft Only Site",
        "description": "Not yet ready for public",
    }, headers=admin_auth)
    assert res.status_code == 200
    site = res.json()
    slug = site["slug"]

    # Public route must be 403 (offline / unpublished)
    pub_res = await client.get(f"/api/public/sites/{slug}")
    assert pub_res.status_code == 403

    # Public search must also be 403
    search_res = await client.get(f"/api/public/sites/{slug}/search?q=test")
    assert search_res.status_code == 403


@pytest.mark.asyncio
async def test_published_snapshot_immutability_and_draft_branching(client: AsyncClient, admin_auth: dict[str, str]):
    """Verify that editing a published website does NOT alter the live published version in place (Rules E & F)."""
    # 1. Create and Publish Version 1
    create_res = await client.post("/api/admin/websites", json={
        "name": "Equipment Catalog",
        "theme": {"primary_color": "#10b981", "preset": "emerald"},
    }, headers=admin_auth)
    site_id = create_res.json()["id"]
    slug = create_res.json()["slug"]

    pub_res = await client.post(f"/api/admin/websites/{site_id}/publish", headers=admin_auth)
    assert pub_res.status_code == 200
    assert pub_res.json()["published_version"] == 1

    # Verify public site serves Version 1 with #10b981
    pub_site = (await client.get(f"/api/public/sites/{slug}")).json()
    assert pub_site["version_number"] == 1
    assert pub_site["theme"]["primary_color"] == "#10b981"

    # 2. Modify Website while Published -> Backend MUST branch a new draft (v2)
    update_res = await client.put(f"/api/admin/websites/{site_id}", json={
        "name": "Equipment Catalog Refactored",
        "theme": {"primary_color": "#ef4444", "preset": "crimson"},
    }, headers=admin_auth)
    assert update_res.status_code == 200
    assert update_res.json()["version_number"] == 2
    assert update_res.json()["version_status"] == "draft"

    # 3. CRITICAL INVARIANT: Public site MUST STILL SERVE Version 1 with #10b981
    pub_site_check = (await client.get(f"/api/public/sites/{slug}")).json()
    assert pub_site_check["version_number"] == 1
    assert pub_site_check["theme"]["primary_color"] == "#10b981"

    # 4. Now Publish Version 2
    pub_v2_res = await client.post(f"/api/admin/websites/{site_id}/publish", headers=admin_auth)
    assert pub_v2_res.status_code == 200
    assert pub_v2_res.json()["published_version"] == 2

    # 5. Now public site serves Version 2
    pub_site_v2 = (await client.get(f"/api/public/sites/{slug}")).json()
    assert pub_site_v2["version_number"] == 2
    assert pub_site_v2["theme"]["primary_color"] == "#ef4444"


@pytest.mark.asyncio
async def test_explicit_document_membership_gating(client: AsyncClient, admin_auth: dict[str, str]):
    """Verify that publishing only exposes documents explicitly added to website membership (Rules G & H)."""
    # 1. Create Website
    create_res = await client.post("/api/admin/websites", json={
        "name": "Warranty Portal",
    }, headers=admin_auth)
    site_id = create_res.json()["id"]
    slug = create_res.json()["slug"]

    # 2. Create 2 Mock Documents directly
    from app.core.database import AsyncSessionLocal
    doc1_id = f"doc-public-{uuid.uuid4().hex[:6]}"
    doc2_id = f"doc-private-{uuid.uuid4().hex[:6]}"

    async with AsyncSessionLocal() as session:
        session.add(Document(
            id=doc1_id,
            filename="public_warranty_001.pdf",
            original_filename="public_warranty_001.pdf",
            file_size_bytes=1024,
            file_hash="hash001",
            storage_path="mock/path1.pdf",
            mime_type="application/pdf",
            status="ready",
        ))
        session.add(Document(
            id=doc2_id,
            filename="private_internal_audit.pdf",
            original_filename="private_internal_audit.pdf",
            file_size_bytes=2048,
            file_hash="hash002",
            storage_path="mock/path2.pdf",
            mime_type="application/pdf",
            status="ready",
        ))
        await session.commit()

    # 3. Explicitly add ONLY doc1 to website membership
    add_mem_res = await client.post(f"/api/admin/websites/{site_id}/documents", json={
        "document_ids": [doc1_id],
        "is_included": True,
        "is_public": True,
    }, headers=admin_auth)
    assert add_mem_res.status_code == 200
    assert add_mem_res.json()["added_count"] == 1

    # 4. Publish Website
    pub_res = await client.post(f"/api/admin/websites/{site_id}/publish", headers=admin_auth)
    assert pub_res.status_code == 200
    assert pub_res.json()["indexed_documents"] == 1

    # 5. Verify doc1 is accessible publicly, but doc2 is 404
    d1_res = await client.get(f"/api/public/sites/{slug}/documents/{doc1_id}")
    assert d1_res.status_code == 200
    assert d1_res.json()["document_id"] == doc1_id

    d2_res = await client.get(f"/api/public/sites/{slug}/documents/{doc2_id}")
    assert d2_res.status_code == 404


@pytest.mark.asyncio
async def test_universal_data_sources_and_multi_domains(client: AsyncClient, admin_auth: dict[str, str]):
    """Verify arbitrary business domains (warranties, certificates, product specs) via Universal DataSource."""
    # 1. Create a "Warranty Management" custom DataSource
    warranty_fields = [
        {"key": "serial_number", "label": "Serial Number", "type": "string", "semantic_role": "identifier"},
        {"key": "product_name", "label": "Product Name", "type": "string", "semantic_role": "title"},
        {"key": "customer", "label": "Customer Name", "type": "string", "semantic_role": "metadata"},
        {"key": "purchase_date", "label": "Purchase Date", "type": "date", "semantic_role": "date"},
        {"key": "expiry_date", "label": "Expiry Date", "type": "date", "semantic_role": "date"},
        {"key": "status", "label": "Warranty Status", "type": "string", "semantic_role": "status"},
    ]
    ds_res = await client.post("/api/admin/data-sources", json={
        "name": "Warranty Records 2026",
        "description": "Customer hardware warranty registry",
        "source_type": "manual",
        "fields": warranty_fields,
    }, headers=admin_auth)
    assert ds_res.status_code == 200
    ds = ds_res.json()
    ds_id = ds["id"]

    # 2. Add records to the DataSource
    rec_res = await client.post(f"/api/admin/data-sources/{ds_id}/records", json={
        "values": {
            "serial_number": "SN-998822",
            "product_name": "Industrial Turbine X-500",
            "customer": "Apex Energy",
            "purchase_date": "2025-01-15",
            "expiry_date": "2028-01-15",
            "status": "Active",
        }
    }, headers=admin_auth)
    assert rec_res.status_code == 200

    # 3. Retrieve DataSource details and verify typed fields & records
    get_ds = await client.get(f"/api/admin/data-sources/{ds_id}", headers=admin_auth)
    assert get_ds.status_code == 200
    ds_detail = get_ds.json()
    assert ds_detail["name"] == "Warranty Records 2026"
    assert len(ds_detail["fields"]) == 6
    assert ds_detail["total_records"] == 1
    assert ds_detail["records"][0]["values"]["serial_number"] == "SN-998822"


@pytest.mark.asyncio
async def test_visual_locator_with_on_the_fly_field_creation(client: AsyncClient, admin_auth: dict[str, str]):
    """Verify Section 8.1 & 63: visual selection can create a new field on the fly and link locator."""
    # Analyze visual selection
    mock_words = [
        {"text": "WARRANTY", "bbox_x": 100, "bbox_y": 50, "bbox_width": 80, "bbox_height": 20, "confidence": 0.98},
        {"text": "EXPIRES:", "bbox_x": 190, "bbox_y": 50, "bbox_width": 60, "bbox_height": 20, "confidence": 0.99},
        {"text": "2029-12-31", "bbox_x": 260, "bbox_y": 50, "bbox_width": 90, "bbox_height": 20, "confidence": 0.97},
    ]
    analysis_res = await client.post("/api/admin/locators/analyze", json={
        "page_width": 1000,
        "page_height": 1400,
        "bbox_x": 260,
        "bbox_y": 50,
        "bbox_width": 90,
        "bbox_height": 20,
        "selected_text": "2029-12-31",
        "page_words": mock_words,
    }, headers=admin_auth)
    assert analysis_res.status_code == 200
    analysis = analysis_res.json()

    # Save locator with on-the-fly new field creation
    save_res = await client.post("/api/admin/locators", json={
        "new_field_name": "Expiration Date",
        "new_field_type": "date",
        "selection_analysis": analysis,
        "pixel_bbox": [260, 50, 90, 20, 1000, 1400],
    }, headers=admin_auth)
    assert save_res.status_code == 200
    loc_data = save_res.json()
    assert loc_data["field_name"] == "Expiration Date"
    assert "compiled_rule_id" in loc_data
    assert len(loc_data["match_explanation"]) > 0
