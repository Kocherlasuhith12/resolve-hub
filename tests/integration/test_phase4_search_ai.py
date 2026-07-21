from typing import Any, cast

import pytest
from httpx import AsyncClient

from resolvehub.app.core.config import get_settings

pytestmark = pytest.mark.integration


async def register_verify_login(
    client: AsyncClient, email: str, display_name: str
) -> dict[str, Any]:
    registration = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Long secure password 123!",
            "display_name": display_name,
        },
    )
    token = registration.json()["verification_token"]
    assert registration.status_code == 202 and token
    assert (
        await client.post("/api/v1/auth/verify-email", json={"token": token})
    ).status_code == 204
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Long secure password 123!"},
    )
    assert login.status_code == 200
    return cast(dict[str, Any], login.json())


def auth(tokens: dict[str, Any]) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def invite_requester(
    client: AsyncClient,
    *,
    organisation_id: str,
    owner_headers: dict[str, str],
    requester_headers: dict[str, str],
    requester_email: str,
    role_id: str,
) -> None:
    invitation = await client.post(
        f"/api/v1/organisations/{organisation_id}/invitations",
        headers=owner_headers,
        json={"email": requester_email, "role_id": role_id},
    )
    assert invitation.status_code == 201
    accepted = await client.post(
        "/api/v1/invitations/accept",
        headers=requester_headers,
        json={"token": invitation.json()["invitation_token"]},
    )
    assert accepted.status_code == 200


async def create_ticket(
    client: AsyncClient,
    *,
    organisation_id: str,
    requester_headers: dict[str, str],
    category_id: str,
    key: str,
    title: str,
    description: str,
    priority: str,
) -> dict[str, Any]:
    response = await client.post(
        f"/api/v1/organisations/{organisation_id}/tickets",
        headers={**requester_headers, "Idempotency-Key": key},
        json={
            "category_id": category_id,
            "title": title,
            "description": description,
            "priority": priority,
        },
    )
    assert response.status_code == 201
    return cast(dict[str, Any], response.json())


@pytest.mark.security
async def test_ticket_search_content_filters_visibility_and_tenant_isolation(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = await register_verify_login(client, "search-owner@example.com", "Search Owner")
    alice = await register_verify_login(client, "search-alice@example.com", "Alice Searcher")
    bob = await register_verify_login(client, "search-bob@example.com", "Bob Requester")
    outsider = await register_verify_login(
        client, "search-outsider@example.com", "Outside Operator"
    )
    owner_headers, alice_headers = auth(owner), auth(alice)
    bob_headers, outsider_headers = auth(bob), auth(outsider)

    organisation = await client.post(
        "/api/v1/organisations",
        headers=owner_headers,
        json={"name": "Search Operations", "slug": "search-operations"},
    )
    organisation_id = organisation.json()["id"]
    roles = await client.get(
        f"/api/v1/organisations/{organisation_id}/roles", headers=owner_headers
    )
    requester_role_id = next(item["id"] for item in roles.json() if item["name"] == "Requester")
    await invite_requester(
        client,
        organisation_id=organisation_id,
        owner_headers=owner_headers,
        requester_headers=alice_headers,
        requester_email="search-alice@example.com",
        role_id=requester_role_id,
    )
    await invite_requester(
        client,
        organisation_id=organisation_id,
        owner_headers=owner_headers,
        requester_headers=bob_headers,
        requester_email="search-bob@example.com",
        role_id=requester_role_id,
    )
    outside_org = await client.post(
        "/api/v1/organisations",
        headers=outsider_headers,
        json={"name": "Outside Search", "slug": "outside-search"},
    )
    assert outside_org.status_code == 201

    department = await client.post(
        f"/api/v1/organisations/{organisation_id}/departments",
        headers=owner_headers,
        json={"name": "Infrastructure"},
    )
    category = await client.post(
        f"/api/v1/organisations/{organisation_id}/categories",
        headers=owner_headers,
        json={
            "department_id": department.json()["id"],
            "name": "Network Connectivity",
            "description": "Routers, wireless access, and campus links",
            "default_priority": "MEDIUM",
        },
    )
    category_id = category.json()["id"]

    outage = await create_ticket(
        client,
        organisation_id=organisation_id,
        requester_headers=alice_headers,
        category_id=category_id,
        key="phase4-search-outage",
        title="Maintenance generator outage",
        description="The diesel alternator stopped beside the library.",
        priority="CRITICAL",
    )
    wifi = await create_ticket(
        client,
        organisation_id=organisation_id,
        requester_headers=alice_headers,
        category_id=category_id,
        key="phase4-search-wifi",
        title="Maintenance request for north wing",
        description="Users cannot connect after the access point restart.",
        priority="HIGH",
    )
    bob_ticket = await create_ticket(
        client,
        organisation_id=organisation_id,
        requester_headers=bob_headers,
        category_id=category_id,
        key="phase4-search-bob",
        title="Maintenance inspection needed",
        description="Routine inspection for the communications cabinet.",
        priority="LOW",
    )
    internal = await client.post(
        f"/api/v1/organisations/{organisation_id}/tickets/{wifi['id']}/comments",
        headers=owner_headers,
        json={"kind": "INTERNAL", "body": "The private keyword is cobaltvalve."},
    )
    assert internal.status_code == 201
    public = await client.post(
        f"/api/v1/organisations/{organisation_id}/tickets/{wifi['id']}/comments",
        headers=owner_headers,
        json={"kind": "PUBLIC", "body": "Tracking public keyword phoenixsignal."},
    )
    assert public.status_code == 201

    search_url = f"/api/v1/organisations/{organisation_id}/search/tickets"
    title_match = await client.get(
        search_url, headers=owner_headers, params={"query": "alternator"}
    )
    assert title_match.status_code == 200
    assert [item["id"] for item in title_match.json()["items"]] == [outage["id"]]

    category_match = await client.get(
        search_url, headers=owner_headers, params={"query": "connectivity"}
    )
    assert {item["id"] for item in category_match.json()["items"]} == {
        outage["id"],
        wifi["id"],
        bob_ticket["id"],
    }
    requester_match = await client.get(
        search_url, headers=owner_headers, params={"query": "Alice Searcher"}
    )
    assert {item["id"] for item in requester_match.json()["items"]} == {
        outage["id"],
        wifi["id"],
    }
    public_match = await client.get(
        search_url, headers=alice_headers, params={"query": "phoenixsignal"}
    )
    assert [item["id"] for item in public_match.json()["items"]] == [wifi["id"]]
    private_hidden = await client.get(
        search_url, headers=alice_headers, params={"query": "cobaltvalve"}
    )
    assert private_hidden.json()["items"] == []
    private_staff_match = await client.get(
        search_url, headers=owner_headers, params={"query": "cobaltvalve"}
    )
    assert [item["id"] for item in private_staff_match.json()["items"]] == [wifi["id"]]

    ai_url = f"/api/v1/organisations/{organisation_id}/tickets/{wifi['id']}/ai/suggestions"
    disabled = await client.post(ai_url, headers=owner_headers)
    assert disabled.status_code == 503
    assert disabled.json()["error"]["code"] == "AI_DISABLED"

    from resolvehub.app.main import app

    enabled_settings = get_settings().model_copy(update={"ai_enabled": True})
    app.dependency_overrides[get_settings] = lambda: enabled_settings
    requester_denied = await client.post(ai_url, headers=alice_headers)
    assert requester_denied.status_code == 403
    outsider_denied = await client.post(ai_url, headers=outsider_headers)
    assert outsider_denied.status_code == 403

    generated = await client.post(ai_url, headers=owner_headers)
    assert generated.status_code == 200
    assert generated.json()["status"] == "SUCCEEDED"
    assert generated.json()["provider"] == "fake"
    suggestions = generated.json()["suggestions"]
    assert {item["kind"] for item in suggestions} == {
        "CATEGORY",
        "PRIORITY",
        "DUPLICATE",
        "SUMMARY",
        "RESPONSE",
    }
    assert all(item["status"] == "PENDING" for item in suggestions)
    priority_suggestion = next(item for item in suggestions if item["kind"] == "PRIORITY")
    decision_url = f"{ai_url}/{priority_suggestion['id']}/decision"
    accepted = await client.post(decision_url, headers=owner_headers, json={"status": "ACCEPTED"})
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "ACCEPTED"
    repeated = await client.post(decision_url, headers=owner_headers, json={"status": "REJECTED"})
    assert repeated.status_code == 409
    unchanged_ticket = await client.get(
        f"/api/v1/organisations/{organisation_id}/tickets/{wifi['id']}",
        headers=owner_headers,
    )
    assert unchanged_ticket.json()["priority"] == wifi["priority"]
    listed_suggestions = await client.get(ai_url, headers=owner_headers)
    assert listed_suggestions.status_code == 200
    assert len(listed_suggestions.json()["items"]) == 5

    class FailingProvider:
        async def suggest(self, context: object) -> object:
            raise RuntimeError("deterministic provider failure")

    from resolvehub.app.modules.ai_assistance import service as ai_service

    monkeypatch.setattr(ai_service, "get_ai_provider", lambda _: FailingProvider())
    provider_failure = await client.post(ai_url, headers=owner_headers)
    assert provider_failure.status_code == 503
    assert provider_failure.json()["error"]["code"] == "AI_UNAVAILABLE"
    ticket_after_failure = await client.get(
        f"/api/v1/organisations/{organisation_id}/tickets/{wifi['id']}",
        headers=owner_headers,
    )
    assert ticket_after_failure.status_code == 200
    app.dependency_overrides.pop(get_settings, None)

    requester_scope = await client.get(
        search_url, headers=alice_headers, params={"query": "maintenance"}
    )
    assert {item["id"] for item in requester_scope.json()["items"]} == {
        outage["id"],
        wifi["id"],
    }
    critical_filter = await client.get(
        search_url,
        headers=owner_headers,
        params={"query": "maintenance", "priority": "CRITICAL"},
    )
    assert [item["id"] for item in critical_filter.json()["items"]] == [outage["id"]]

    first_page = await client.get(
        search_url,
        headers=owner_headers,
        params={"query": "maintenance", "limit": 1},
    )
    assert len(first_page.json()["items"]) == 1
    assert first_page.json()["next_cursor"]
    second_page = await client.get(
        search_url,
        headers=owner_headers,
        params={
            "query": "maintenance",
            "limit": 1,
            "cursor": first_page.json()["next_cursor"],
        },
    )
    assert len(second_page.json()["items"]) == 1
    assert second_page.json()["items"][0]["id"] != first_page.json()["items"][0]["id"]

    denied = await client.get(search_url, headers=outsider_headers, params={"query": "maintenance"})
    assert denied.status_code == 403
    too_short = await client.get(search_url, headers=owner_headers, params={"query": "x"})
    assert too_short.status_code == 422
