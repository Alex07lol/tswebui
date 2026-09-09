"""Integration tests for Teach From Examples session service and API."""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.services.teach.teach_service import TeachService


def test_teach_service_start_and_analyze():
    session = TeachService.start_session(["doc-1", "doc-2"])
    assert session.status == "uploaded"

    mock_doc_map = {
        "doc-1": "Invoice # INV-2026-001\nTotal: $1,200.00\nDate: 01/15/2026",
        "doc-2": "Invoice # INV-2026-002\nTotal: $3,450.00\nDate: 02/20/2026",
    }
    analyzed = TeachService.analyze(session.session_id, mock_doc_map)
    assert analyzed.status == "completed"
    assert len(analyzed.layouts) >= 1
    assert analyzed.layouts[0].label.startswith("Layout")
    assert len(analyzed.proposals) >= 1
    assert analyzed.proposals[0].confidence_label in ["Very High", "High"]


@pytest.mark.asyncio
async def test_teach_api_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create a dummy teach session directly in service for API test
        s = TeachService.start_session(["mock-doc-1"])
        TeachService.analyze(s.session_id, {"mock-doc-1": "Invoice # INV-2026-001\nTotal: $50.00"})

        # 2. Get layouts
        l_resp = await client.get(f"/api/teach/{s.session_id}/layouts")
        assert l_resp.status_code == 200
        assert "layouts" in l_resp.json()

        # 3. Get proposals
        p_resp = await client.get(f"/api/teach/{s.session_id}/proposals")
        assert p_resp.status_code == 200
        proposals = p_resp.json()["proposals"]
        assert len(proposals) >= 1

        # 4. Save setup from teach session
        save_resp = await client.post(
            f"/api/teach/{s.session_id}/save-setup",
            json={"setup_name": "Discovered Invoices Setup"},
        )
        assert save_resp.status_code == 201
        saved = save_resp.json()
        assert saved["name"] == "Discovered Invoices Setup"
        assert saved["field_count"] >= 1
