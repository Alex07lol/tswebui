"""Tests for authentication, RBAC, and audit logging."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.database import create_all_tables


@pytest.mark.anyio
async def test_auth_registration_and_login_flow(client: AsyncClient) -> None:
    """Test user registration, login, profile fetch, and audit logs."""
    await create_all_tables()

    # 1. Register new user
    reg_payload = {
        "email": "test_engineer@example.com",
        "password": "securepassword123",
        "full_name": "Test Engineer",
        "role": "editor",
    }
    reg_resp = await client.post("/api/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()
    assert user_data["email"] == "test_engineer@example.com"
    assert user_data["role"] == "editor"
    assert user_data["is_active"] is True
    assert "hashed_password" not in user_data

    # 2. Prevent duplicate registration
    dup_resp = await client.post("/api/auth/register", json=reg_payload)
    assert dup_resp.status_code == 400

    # 3. Login with correct credentials
    login_payload = {
        "email": "test_engineer@example.com",
        "password": "securepassword123",
    }
    login_resp = await client.post("/api/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    token = token_data["access_token"]
    assert token_data["token_type"] == "bearer"
    assert token_data["user"]["email"] == "test_engineer@example.com"

    # 4. Login with incorrect password
    bad_login_resp = await client.post(
        "/api/auth/login",
        json={"email": "test_engineer@example.com", "password": "wrongpassword"},
    )
    assert bad_login_resp.status_code == 401

    # 5. Access protected /api/auth/me with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = await client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "test_engineer@example.com"
    assert me_data["role"] == "editor"

    # 6. Verify audit logs recorded registration and login events
    audit_resp = await client.get("/api/audit-logs")
    assert audit_resp.status_code == 200
    logs = audit_resp.json()
    event_types = [l["event_type"] for l in logs]
    assert "user.registered" in event_types
    assert "user.login" in event_types
