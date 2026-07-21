from typing import Any, cast

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


async def register_verify_login(client: AsyncClient, email: str) -> dict[str, Any]:
    registration = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Long secure password 123!", "display_name": email},
    )
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


def auth(tokens: dict[str, Any]) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def invite_as_role(
    client: AsyncClient,
    *,
    organisation_id: str,
    owner_headers: dict[str, str],
    member_headers: dict[str, str],
    email: str,
    role_id: str,
) -> None:
    invitation = await client.post(
        f"/api/v1/organisations/{organisation_id}/invitations",
        headers=owner_headers,
        json={"email": email, "role_id": role_id},
    )
    assert invitation.status_code == 201
    accepted = await client.post(
        "/api/v1/invitations/accept",
        headers=member_headers,
        json={"token": invitation.json()["invitation_token"]},
    )
    assert accepted.status_code == 200


@pytest.mark.security
async def test_ticket_lifecycle_idempotency_visibility_and_tenant_isolation(
    client: AsyncClient,
) -> None:
    owner = await register_verify_login(client, "phase2-owner@example.com")
    agent = await register_verify_login(client, "phase2-agent@example.com")
    requester = await register_verify_login(client, "phase2-requester@example.com")
    outsider = await register_verify_login(client, "phase2-outsider@example.com")
    owner_headers, agent_headers = auth(owner), auth(agent)
    requester_headers, outsider_headers = auth(requester), auth(outsider)

    organisation = await client.post(
        "/api/v1/organisations",
        headers=owner_headers,
        json={"name": "Ticket Operations", "slug": "ticket-operations"},
    )
    organisation_id = organisation.json()["id"]
    roles = await client.get(
        f"/api/v1/organisations/{organisation_id}/roles", headers=owner_headers
    )
    role_ids = {item["name"]: item["id"] for item in roles.json()}
    await invite_as_role(
        client,
        organisation_id=organisation_id,
        owner_headers=owner_headers,
        member_headers=agent_headers,
        email="phase2-agent@example.com",
        role_id=role_ids["Agent"],
    )
    await invite_as_role(
        client,
        organisation_id=organisation_id,
        owner_headers=owner_headers,
        member_headers=requester_headers,
        email="phase2-requester@example.com",
        role_id=role_ids["Requester"],
    )
    outsider_org = await client.post(
        "/api/v1/organisations",
        headers=outsider_headers,
        json={"name": "Outside Org", "slug": "outside-org"},
    )
    assert outsider_org.status_code == 201

    agent_membership = await client.get(
        f"/api/v1/organisations/{organisation_id}/membership/me", headers=agent_headers
    )
    assert agent_membership.status_code == 200
    assert agent_membership.json()["role_name"] == "Agent"
    assert "ticket:assign" in agent_membership.json()["permissions"]
    outsider_membership = await client.get(
        f"/api/v1/organisations/{organisation_id}/membership/me", headers=outsider_headers
    )
    assert outsider_membership.status_code == 403
    candidates = await client.get(
        f"/api/v1/organisations/{organisation_id}/tickets/assignment-candidates",
        headers=agent_headers,
    )
    assert candidates.status_code == 200
    candidate_ids = {item["user_id"] for item in candidates.json()}
    assert (await client.get("/api/v1/auth/me", headers=owner_headers)).json()[
        "id"
    ] in candidate_ids
    assert (await client.get("/api/v1/auth/me", headers=agent_headers)).json()[
        "id"
    ] in candidate_ids
    requester_candidates = await client.get(
        f"/api/v1/organisations/{organisation_id}/tickets/assignment-candidates",
        headers=requester_headers,
    )
    assert requester_candidates.status_code == 403
    outsider_candidates = await client.get(
        f"/api/v1/organisations/{organisation_id}/tickets/assignment-candidates",
        headers=outsider_headers,
    )
    assert outsider_candidates.status_code == 403

    department = await client.post(
        f"/api/v1/organisations/{organisation_id}/departments",
        headers=owner_headers,
        json={"name": "Facilities"},
    )
    category = await client.post(
        f"/api/v1/organisations/{organisation_id}/categories",
        headers=owner_headers,
        json={
            "department_id": department.json()["id"],
            "name": "Plumbing",
            "default_priority": "HIGH",
        },
    )
    assert category.status_code == 201

    ticket_payload = {
        "category_id": category.json()["id"],
        "title": "Water leakage near hostel block",
        "description": "A pipe is leaking continuously beside the entrance.",
        "source": "WEB",
    }
    create_headers = {**requester_headers, "Idempotency-Key": "leak-report-0001"}
    created = await client.post(
        f"/api/v1/organisations/{organisation_id}/tickets",
        headers=create_headers,
        json=ticket_payload,
    )
    assert created.status_code == 201
    assert created.json()["priority"] == "HIGH"
    assert created.json()["status"] == "SUBMITTED"
    ticket_id = created.json()["id"]
    replay = await client.post(
        f"/api/v1/organisations/{organisation_id}/tickets",
        headers=create_headers,
        json=ticket_payload,
    )
    assert replay.status_code == 200
    assert replay.json()["id"] == ticket_id
    mismatched = await client.post(
        f"/api/v1/organisations/{organisation_id}/tickets",
        headers=create_headers,
        json={**ticket_payload, "title": "Different payload"},
    )
    assert mismatched.status_code == 409
    assert mismatched.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"

    requester_list = await client.get(
        f"/api/v1/organisations/{organisation_id}/tickets", headers=requester_headers
    )
    assert [item["id"] for item in requester_list.json()["items"]] == [ticket_id]
    cross_tenant = await client.get(
        f"/api/v1/organisations/{organisation_id}/tickets/{ticket_id}",
        headers=outsider_headers,
    )
    assert cross_tenant.status_code == 403

    assigned = await client.post(
        f"/api/v1/organisations/{organisation_id}/tickets/{ticket_id}/assignment",
        headers=owner_headers,
        json={
            "assigned_agent_id": (
                await client.get("/api/v1/auth/me", headers=agent_headers)
            ).json()["id"],
            "version": 1,
        },
    )
    assert assigned.status_code == 200
    assert assigned.json()["version"] == 2
    conflict = await client.post(
        f"/api/v1/organisations/{organisation_id}/tickets/{ticket_id}/assignment",
        headers=owner_headers,
        json={"assigned_agent_id": assigned.json()["assigned_agent_id"], "version": 1},
    )
    assert conflict.status_code == 409

    version = 2
    for next_status in ("TRIAGED", "ASSIGNED", "IN_PROGRESS"):
        transitioned = await client.post(
            f"/api/v1/organisations/{organisation_id}/tickets/{ticket_id}/transitions",
            headers=agent_headers,
            json={"status": next_status, "version": version},
        )
        assert transitioned.status_code == 200
        version = transitioned.json()["version"]
    invalid_transition = await client.post(
        f"/api/v1/organisations/{organisation_id}/tickets/{ticket_id}/transitions",
        headers=agent_headers,
        json={"status": "CLOSED", "version": version},
    )
    assert invalid_transition.status_code == 409

    internal = await client.post(
        f"/api/v1/organisations/{organisation_id}/tickets/{ticket_id}/comments",
        headers=agent_headers,
        json={"kind": "INTERNAL", "body": "Valve access requires the facilities key."},
    )
    assert internal.status_code == 201
    public = await client.post(
        f"/api/v1/organisations/{organisation_id}/tickets/{ticket_id}/comments",
        headers=agent_headers,
        json={"kind": "PUBLIC", "body": "An agent is inspecting the leak."},
    )
    assert public.status_code == 201
    requester_comments = await client.get(
        f"/api/v1/organisations/{organisation_id}/tickets/{ticket_id}/comments",
        headers=requester_headers,
    )
    assert [item["kind"] for item in requester_comments.json()["items"]] == ["PUBLIC"]
    requester_timeline = await client.get(
        f"/api/v1/organisations/{organisation_id}/tickets/{ticket_id}/timeline",
        headers=requester_headers,
    )
    assert "INTERNAL_NOTE_ADDED" not in {
        item["event_type"] for item in requester_timeline.json()["items"]
    }
    forbidden_note = await client.post(
        f"/api/v1/organisations/{organisation_id}/tickets/{ticket_id}/comments",
        headers=requester_headers,
        json={"kind": "INTERNAL", "body": "Should not be accepted"},
    )
    assert forbidden_note.status_code == 403

    attachment = await client.post(
        f"/api/v1/organisations/{organisation_id}/tickets/{ticket_id}/attachments",
        headers=agent_headers,
        json={"filename": "leak.jpg", "content_type": "image/jpeg", "size_bytes": 2048},
    )
    assert attachment.status_code == 201
    forbidden_attachment = await client.post(
        f"/api/v1/organisations/{organisation_id}/tickets/{ticket_id}/attachments",
        headers=agent_headers,
        json={
            "filename": "payload.exe",
            "content_type": "application/octet-stream",
            "size_bytes": 10,
        },
    )
    assert forbidden_attachment.status_code == 422

    resolved = await client.post(
        f"/api/v1/organisations/{organisation_id}/tickets/{ticket_id}/transitions",
        headers=agent_headers,
        json={"status": "RESOLVED", "version": version},
    )
    assert resolved.status_code == 200
    assert resolved.json()["resolved_at"] is not None


async def test_ticket_cursor_pagination(client: AsyncClient) -> None:
    owner = await register_verify_login(client, "pagination-owner@example.com")
    headers = auth(owner)
    organisation = await client.post(
        "/api/v1/organisations",
        headers=headers,
        json={"name": "Pagination Org", "slug": "pagination-org"},
    )
    organisation_id = organisation.json()["id"]
    department = await client.post(
        f"/api/v1/organisations/{organisation_id}/departments",
        headers=headers,
        json={"name": "IT"},
    )
    category = await client.post(
        f"/api/v1/organisations/{organisation_id}/categories",
        headers=headers,
        json={"department_id": department.json()["id"], "name": "Internet"},
    )
    for number in range(2):
        response = await client.post(
            f"/api/v1/organisations/{organisation_id}/tickets",
            headers={**headers, "Idempotency-Key": f"pagination-{number}"},
            json={
                "category_id": category.json()["id"],
                "title": f"Internet issue {number}",
                "description": "Connectivity is intermittent in the office.",
            },
        )
        assert response.status_code == 201
    first_page = await client.get(
        f"/api/v1/organisations/{organisation_id}/tickets?limit=1", headers=headers
    )
    assert len(first_page.json()["items"]) == 1
    cursor = first_page.json()["next_cursor"]
    assert cursor
    second_page = await client.get(
        f"/api/v1/organisations/{organisation_id}/tickets?limit=1&cursor={cursor}",
        headers=headers,
    )
    assert len(second_page.json()["items"]) == 1
    assert second_page.json()["items"][0]["id"] != first_page.json()["items"][0]["id"]
