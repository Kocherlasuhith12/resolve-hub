from typing import Any, cast
from uuid import uuid4

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


async def register_verify_login(client: AsyncClient, email: str) -> dict[str, Any]:
    registration = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Long secure password 123!", "display_name": email},
    )
    assert registration.status_code == 202
    token = registration.json()["verification_token"]
    assert token
    assert (
        await client.post("/api/v1/auth/verify-email", json={"token": token})
    ).status_code == 204
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Long secure password 123!"}
    )
    assert login.status_code == 200
    return cast(dict[str, Any], login.json())


@pytest.mark.asyncio
async def test_member_role_and_status_update(client: AsyncClient) -> None:
    owner_email = f"owner-{uuid4()}@example.com"
    tokens = await register_verify_login(client, owner_email)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    org_resp = await client.post(
        "/api/v1/organisations",
        headers=headers,
        json={"name": f"Org {uuid4()}", "slug": f"org-{uuid4()}"},
    )
    assert org_resp.status_code == 201
    org_id = org_resp.json()["id"]

    roles_resp = await client.get(f"/api/v1/organisations/{org_id}/roles", headers=headers)
    assert roles_resp.status_code == 200
    roles = roles_resp.json()
    requester_role = next(r for r in roles if r["name"] == "Requester")

    members_resp = await client.get(f"/api/v1/organisations/{org_id}/members", headers=headers)
    assert members_resp.status_code == 200
    members = members_resp.json()
    my_member = members[0]

    # Deactivating the only admin should fail
    deactivate_resp = await client.patch(
        f"/api/v1/organisations/{org_id}/members/{my_member['id']}/status",
        headers=headers,
        json={"is_active": False},
    )
    assert deactivate_resp.status_code == 400
    assert deactivate_resp.json()["error"]["code"] == "CANNOT_DEACTIVATE_LAST_ADMIN"

    # Demoting the only admin should fail
    demote_resp = await client.patch(
        f"/api/v1/organisations/{org_id}/members/{my_member['id']}/role",
        headers=headers,
        json={"role_id": requester_role["id"]},
    )
    assert demote_resp.status_code == 400
    assert demote_resp.json()["error"]["code"] == "CANNOT_REMOVE_LAST_ADMIN"


@pytest.mark.asyncio
async def test_analytics_summary_and_csv_export(client: AsyncClient) -> None:
    owner_email = f"owner-{uuid4()}@example.com"
    tokens = await register_verify_login(client, owner_email)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    org_resp = await client.post(
        "/api/v1/organisations",
        headers=headers,
        json={"name": f"Org {uuid4()}", "slug": f"org-{uuid4()}"},
    )
    assert org_resp.status_code == 201
    org_id = org_resp.json()["id"]

    # Summary
    summary_resp = await client.get(
        f"/api/v1/organisations/{org_id}/analytics/summary", headers=headers
    )
    assert summary_resp.status_code == 200
    data = summary_resp.json()
    assert "total_tickets" in data
    assert "sla_compliance_percent" in data

    # CSV Export
    csv_resp = await client.get(
        f"/api/v1/organisations/{org_id}/analytics/exports/tickets", headers=headers
    )
    assert csv_resp.status_code == 200
    assert csv_resp.headers["content-type"].startswith("text/csv")
    assert "ticket_number" in csv_resp.text


@pytest.mark.asyncio
async def test_api_key_lifecycle(client: AsyncClient) -> None:
    owner_email = f"owner-{uuid4()}@example.com"
    tokens = await register_verify_login(client, owner_email)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    org_resp = await client.post(
        "/api/v1/organisations",
        headers=headers,
        json={"name": f"Org {uuid4()}", "slug": f"org-{uuid4()}"},
    )
    assert org_resp.status_code == 201
    org_id = org_resp.json()["id"]

    # Create key
    create_resp = await client.post(
        f"/api/v1/organisations/{org_id}/api-keys",
        headers=headers,
        json={"name": "Integration Test Key", "scopes": "*"},
    )
    assert create_resp.status_code == 201
    key_data = create_resp.json()
    assert key_data["raw_key"] is not None
    assert key_data["name"] == "Integration Test Key"

    # List keys
    list_resp = await client.get(f"/api/v1/organisations/{org_id}/api-keys", headers=headers)
    assert list_resp.status_code == 200
    keys = list_resp.json()
    assert any(k["id"] == key_data["id"] for k in keys)

    # Revoke key
    revoke_resp = await client.delete(
        f"/api/v1/organisations/{org_id}/api-keys/{key_data['id']}", headers=headers
    )
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["revoked_at"] is not None


@pytest.mark.asyncio
async def test_webhook_lifecycle(client: AsyncClient) -> None:
    owner_email = f"owner-{uuid4()}@example.com"
    tokens = await register_verify_login(client, owner_email)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    org_resp = await client.post(
        "/api/v1/organisations",
        headers=headers,
        json={"name": f"Org {uuid4()}", "slug": f"org-{uuid4()}"},
    )
    assert org_resp.status_code == 201
    org_id = org_resp.json()["id"]

    # Create webhook
    create_resp = await client.post(
        f"/api/v1/organisations/{org_id}/webhooks",
        headers=headers,
        json={"url": "https://example.com/webhook", "events": "ticket.*"},
    )
    assert create_resp.status_code == 201
    wh_data = create_resp.json()
    assert wh_data["raw_secret"] is not None

    # List webhooks
    list_resp = await client.get(f"/api/v1/organisations/{org_id}/webhooks", headers=headers)
    assert list_resp.status_code == 200
    assert any(w["id"] == wh_data["id"] for w in list_resp.json())

    # Test ping
    ping_resp = await client.post(
        f"/api/v1/organisations/{org_id}/webhooks/{wh_data['id']}/test",
        headers=headers,
    )
    assert ping_resp.status_code == 200
    assert ping_resp.json()["event_type"] == "ping"

    # Delete webhook
    delete_resp = await client.delete(
        f"/api/v1/organisations/{org_id}/webhooks/{wh_data['id']}",
        headers=headers,
    )
    assert delete_resp.status_code == 204
