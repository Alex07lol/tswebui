"""Integration tests for Setup & Field consumer API endpoints."""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_create_setup_and_add_field_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create a setup
        resp = await client.post(
            "/api/setups",
            json={"name": "Laptop Warranty Documents", "description": "Warranty cards and invoices"},
        )
        assert resp.status_code == 201
        setup = resp.json()
        assert setup["name"] == "Laptop Warranty Documents"
        setup_id = setup["id"]

        # 2. Add a field using human pattern
        f_resp = await client.post(
            f"/api/setups/{setup_id}/fields",
            json={
                "display_name": "Serial Number",
                "human_pattern": "SN-{YYYY}-{NNNNNN}",
                "examples": ["SN-2026-001234"],
            },
        )
        assert f_resp.status_code == 201
        field_data = f_resp.json()
        assert field_data["field_id"] == "serial_number"
        assert field_data["confidence_label"] in ["Very High", "High"]
        assert field_data["status"] == "ready"

        # 3. List fields for this setup
        list_f = await client.get(f"/api/setups/{setup_id}/fields")
        assert list_f.status_code == 200
        fields = list_f.json()
        assert len(fields) >= 1
        assert fields[0]["field_id"] == "serial_number"

        # 4. Get advanced configuration for Advanced Rule Editor
        adv_resp = await client.get(f"/api/setups/{setup_id}/fields/serial_number/advanced")
        assert adv_resp.status_code == 200
        adv = adv_resp.json()
        assert "rules" in adv
        assert len(adv["rules"]) > 0

        # 5. List setups in consumer format
        s_list = await client.get("/api/setups")
        assert s_list.status_code == 200
        setups = s_list.json()
        assert any(s["id"] == setup_id for s in setups)


@pytest.mark.asyncio
async def test_pattern_parser_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Compile
        c_resp = await client.post(
            "/api/pattern-parser/compile",
            json={"human_pattern": "INV-{YYYY}-{NNNNN}", "ocr_tolerant": True},
        )
        assert c_resp.status_code == 200
        c_data = c_resp.json()
        assert r"\d{4}" in c_data["regex"]
        assert c_data["inferred_type"] == "text"

        # From examples
        ex_resp = await client.post(
            "/api/pattern-parser/from-examples",
            json={"examples": ["01/15/2026", "02/18/2026"]},
        )
        assert ex_resp.status_code == 200
        ex_data = ex_resp.json()
        assert ex_data["inferred_human_pattern"] in ["{MM}/{DD}/{YYYY}", "{DD}/{MM}/{YYYY}"]
        assert ex_data["inferred_type"] == "date"
