"""Tests for Document Website platform, Visual Locators, Search Provider, and Public APIs."""
from __future__ import annotations

import json
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.core.database import create_all_tables, AsyncSessionLocal
from app.services.locators import analyze_pdf_selection, learn_generalized_locator
from app.providers.search.database import DatabaseSearchProvider


@pytest.fixture(autouse=True)
async def setup_db():
    await create_all_tables()


@pytest.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_website_and_publish_flow(client: AsyncClient):
    """Test full admin website lifecycle: creation, update, collection, and publishing."""
    # 1. Create Website
    create_payload = {
        "name": "Engineering Drawing Library",
        "description": "Public drawing repository for plant expansion",
        "theme": {"preset": "engineering_dark", "primary_color": "#0284c7"},
        "search_config": {"searchable_fields": ["title", "drawing_number", "project"]},
        "field_mappings": {"title_field": "title", "drawing_number_field": "drawing_number"},
    }
    resp = await client.post("/api/admin/websites", json=create_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["name"] == "Engineering Drawing Library"
    assert data["status"] == "draft"
    site_id = data["id"]
    slug = data["slug"]

    # 2. Add Collection
    coll_resp = await client.post(f"/api/admin/websites/{site_id}/collections", json={
        "name": "Pump Room Drawings",
        "description": "Mechanical pump equipment layouts",
        "filter_query": {"field": "discipline", "value": "Mechanical"},
    })
    assert coll_resp.status_code == 200
    assert coll_resp.json()["status"] == "ok"

    # 3. Before publish, public route should be 403
    pub_check = await client.get(f"/api/public/sites/{slug}")
    assert pub_check.status_code == 403

    # 4. Publish Website
    pub_resp = await client.post(f"/api/admin/websites/{site_id}/publish")
    assert pub_resp.status_code == 200
    pub_data = pub_resp.json()
    assert pub_data["status"] == "published"
    assert pub_data["published_version"] == 1

    # 5. Now public route must return published site config
    site_pub = await client.get(f"/api/public/sites/{slug}")
    assert site_pub.status_code == 200
    public_site = site_pub.json()
    assert public_site["name"] == "Engineering Drawing Library"
    assert public_site["theme"]["primary_color"] == "#0284c7"
    assert len(public_site["collections"]) == 1
    assert public_site["collections"][0]["name"] == "Pump Room Drawings"

    # 6. Unpublish
    unpub = await client.post(f"/api/admin/websites/{site_id}/unpublish")
    assert unpub.status_code == 200
    assert unpub.json()["status"] == "unpublished"

    # 7. Check public route is 403 again
    offline_check = await client.get(f"/api/public/sites/{slug}")
    assert offline_check.status_code == 403


@pytest.mark.asyncio
async def test_locator_selection_analysis():
    """Test visual selection analysis computes relative boxes and anchor candidates."""
    mock_words = [
        {"text": "DRAWING", "bbox_x": 50, "bbox_y": 100, "bbox_width": 60, "bbox_height": 20, "confidence": 0.98},
        {"text": "TITLE:", "bbox_x": 115, "bbox_y": 100, "bbox_width": 45, "bbox_height": 20, "confidence": 0.97},
        {"text": "PUMP", "bbox_x": 200, "bbox_y": 100, "bbox_width": 40, "bbox_height": 20, "confidence": 0.99},
        {"text": "ROOM", "bbox_x": 245, "bbox_y": 100, "bbox_width": 45, "bbox_height": 20, "confidence": 0.99},
    ]

    analysis = analyze_pdf_selection(
        page_width=1000,
        page_height=1500,
        bbox_x=200,
        bbox_y=100,
        bbox_width=90,
        bbox_height=20,
        selected_text="PUMP ROOM",
        page_words=mock_words,
    )

    assert analysis["selected_text"] == "PUMP ROOM"
    assert analysis["rel_x"] == 0.2
    assert analysis["rel_y"] == round(100 / 1500, 4)
    assert any("TITLE" in a for a in analysis["anchor_candidates"])
    assert analysis["structure_config"]["same_line"] is True
    assert analysis["structure_config"]["word_count"] == 2


@pytest.mark.asyncio
async def test_multi_example_locator_learning():
    """Test multi-example locator learning aggregates regions and common anchors."""
    examples = [
        {
            "selected_text": "PUMP ROOM 1",
            "bbox_x": 200,
            "bbox_y": 100,
            "bbox_width": 100,
            "bbox_height": 20,
            "page_width": 1000,
            "page_height": 1000,
            "nearby_labels": ["TITLE:", "DRAWING"],
        },
        {
            "selected_text": "BOILER ROOM 2",
            "bbox_x": 210,
            "bbox_y": 105,
            "bbox_width": 110,
            "bbox_height": 20,
            "page_width": 1000,
            "page_height": 1000,
            "nearby_labels": ["TITLE:", "PROJECT"],
        },
    ]

    learned = learn_generalized_locator(examples)
    assert "rel_x" in learned
    assert 0.19 <= learned["rel_x"] <= 0.22
    assert "TITLE:" in learned["anchor_candidates"]
    assert learned["structure_config"]["example_count"] == 2


@pytest.mark.asyncio
async def test_search_provider_ranking():
    """Test 5-tier search ranking: exact title > title prefix > structured field > full text."""
    import uuid
    async with AsyncSessionLocal() as s:
        provider = DatabaseSearchProvider(s)
        test_site_id = f"test-site-{uuid.uuid4().hex[:6]}"
        d1 = f"doc-{uuid.uuid4().hex[:6]}"
        d2 = f"doc-{uuid.uuid4().hex[:6]}"
        d3 = f"doc-{uuid.uuid4().hex[:6]}"

        # Index 3 mock documents
        await provider.index_document(
            document_id=d1,
            website_id=test_site_id,
            title="Pump Room Layout",
            drawing_number="DWG-001",
            full_text="Some electrical schematic text",
            structured_fields={"project": "Plant Expansion"},
        )
        await provider.index_document(
            document_id=d2,
            website_id=test_site_id,
            title="Pump House Foundation",
            drawing_number="DWG-002",
            full_text="Structural concrete details",
            structured_fields={"project": "Plant Expansion"},
        )
        await provider.index_document(
            document_id=d3,
            website_id=test_site_id,
            title="Main Substation",
            drawing_number="DWG-003",
            full_text="This drawing mentions a pump room auxiliary unit",
            structured_fields={"project": "Power Grid"},
        )

        # Mark all 3 documents public for this test site
        from app.models.website import DocumentVisibility
        from datetime import datetime, timezone
        for d in [d1, d2, d3]:
            s.add(DocumentVisibility(
                id=str(uuid.uuid4()),
                document_id=d,
                website_id=test_site_id,
                is_public=True,
                published_at=datetime.now(timezone.utc),
            ))
        await s.commit()

        # Query: "Pump Room Layout" -> exact match d1 should rank #1
        res = await provider.search(website_id=test_site_id, query="Pump Room Layout")
        assert res.total >= 1
        assert res.hits[0].document_id == d1
        assert res.hits[0].rank_tier == "exact_title"
        assert res.hits[0].score == 1.0

        # Query: "Pump" -> d1 and d2 should outrank d3 (which only has it in full OCR text)
        res_prefix = await provider.search(website_id=test_site_id, query="Pump")
        assert len(res_prefix.hits) >= 2
        hit_ids = [h.document_id for h in res_prefix.hits]
        assert hit_ids.index(d1) < hit_ids.index(d3)
        assert hit_ids.index(d2) < hit_ids.index(d3)
