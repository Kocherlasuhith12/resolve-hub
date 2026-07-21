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


async def register_and_verify(client: AsyncClient, email: str) -> None:
    registration = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Long secure password 123!", "display_name": email},
    )
    token = registration.json()["verification_token"]
    assert registration.status_code == 202
    assert token
    assert (
        await client.post("/api/v1/auth/verify-email", json={"token": token})
    ).status_code == 204


@pytest.mark.security
async def test_identity_tenancy_invitation_and_department_flow(client: AsyncClient) -> None:
    owner_tokens = await register_verify_login(client, "owner@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_tokens['access_token']}"}
    organisation = await client.post(
        "/api/v1/organisations",
        headers=owner_headers,
        json={"name": "Alpha Services", "slug": "alpha-services"},
    )
    assert organisation.status_code == 201
    organisation_id = organisation.json()["id"]
    roles = await client.get(
        f"/api/v1/organisations/{organisation_id}/roles", headers=owner_headers
    )
    assert roles.status_code == 200
    role_id = next(item["id"] for item in roles.json() if item["name"] == "Organisation Admin")
    initial_members = await client.get(
        f"/api/v1/organisations/{organisation_id}/members", headers=owner_headers
    )
    assert initial_members.status_code == 200
    assert [item["email"] for item in initial_members.json()] == ["owner@example.com"]

    member_tokens = await register_verify_login(client, "member@example.com")
    member_headers = {"Authorization": f"Bearer {member_tokens['access_token']}"}
    invitation = await client.post(
        f"/api/v1/organisations/{organisation_id}/invitations",
        headers=owner_headers,
        json={"email": "member@example.com", "role_id": role_id},
    )
    assert invitation.status_code == 201
    first_token = invitation.json()["invitation_token"]
    history = await client.get(
        f"/api/v1/organisations/{organisation_id}/invitations", headers=owner_headers
    )
    assert history.status_code == 200
    assert history.json()[0]["status"] == "PENDING"
    assert history.json()[0]["invitation_token"] is None
    resent = await client.post(
        f"/api/v1/organisations/{organisation_id}/invitations/{invitation.json()['id']}/resend",
        headers=owner_headers,
    )
    assert resent.status_code == 200
    assert resent.json()["invitation_token"] != first_token
    old_token_rejected = await client.post(
        "/api/v1/invitations/accept",
        headers=member_headers,
        json={"token": first_token},
    )
    assert old_token_rejected.status_code == 400
    accepted = await client.post(
        "/api/v1/invitations/accept",
        headers=member_headers,
        json={"token": resent.json()["invitation_token"]},
    )
    assert accepted.status_code == 200
    accepted_history = await client.get(
        f"/api/v1/organisations/{organisation_id}/invitations", headers=owner_headers
    )
    assert accepted_history.json()[0]["status"] == "ACCEPTED"
    accepted_revoke = await client.post(
        f"/api/v1/organisations/{organisation_id}/invitations/{invitation.json()['id']}/revoke",
        headers=owner_headers,
    )
    assert accepted_revoke.status_code == 409
    revoked_invitation = await client.post(
        f"/api/v1/organisations/{organisation_id}/invitations",
        headers=owner_headers,
        json={"email": "revoked@example.com", "role_id": role_id},
    )
    revoked = await client.post(
        f"/api/v1/organisations/{organisation_id}/invitations/{revoked_invitation.json()['id']}/revoke",
        headers=owner_headers,
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "REVOKED"
    revoked_resend = await client.post(
        f"/api/v1/organisations/{organisation_id}/invitations/{revoked_invitation.json()['id']}/resend",
        headers=owner_headers,
    )
    assert revoked_resend.status_code == 409
    members = await client.get(
        f"/api/v1/organisations/{organisation_id}/members", headers=owner_headers
    )
    assert {item["email"] for item in members.json()} == {
        "owner@example.com",
        "member@example.com",
    }
    department = await client.post(
        f"/api/v1/organisations/{organisation_id}/departments",
        headers=member_headers,
        json={"name": "Facilities", "description": "Building operations"},
    )
    assert department.status_code == 201

    outsider_tokens = await register_verify_login(client, "outsider@example.com")
    outsider_headers = {"Authorization": f"Bearer {outsider_tokens['access_token']}"}
    denied = await client.get(
        f"/api/v1/organisations/{organisation_id}/departments", headers=outsider_headers
    )
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"
    assert (
        await client.get(
            f"/api/v1/organisations/{organisation_id}/members", headers=outsider_headers
        )
    ).status_code == 403
    assert (
        await client.get(
            f"/api/v1/organisations/{organisation_id}/invitations", headers=outsider_headers
        )
    ).status_code == 403
    assert (
        await client.post(
            f"/api/v1/organisations/{organisation_id}/invitations/{revoked_invitation.json()['id']}/resend",
            headers=outsider_headers,
        )
    ).status_code == 403


@pytest.mark.security
async def test_refresh_rotation_reuse_revokes_family(client: AsyncClient) -> None:
    tokens = await register_verify_login(client, "rotation@example.com")
    first_refresh = tokens["refresh_token"]
    rotated = await client.post("/api/v1/auth/refresh", json={"refresh_token": first_refresh})
    assert rotated.status_code == 200
    second_refresh = rotated.json()["refresh_token"]

    replay = await client.post("/api/v1/auth/refresh", json={"refresh_token": first_refresh})
    assert replay.status_code == 401
    assert replay.json()["error"]["code"] == "REFRESH_TOKEN_REUSED"
    family_revoked = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": second_refresh}
    )
    assert family_revoked.status_code == 401


@pytest.mark.security
async def test_browser_session_uses_httponly_refresh_and_csrf_rotation(
    client: AsyncClient,
) -> None:
    await register_and_verify(client, "browser-session@example.com")
    login = await client.post(
        "/api/v1/auth/browser/login",
        headers={"X-ResolveHub-Client": "browser"},
        json={
            "email": "browser-session@example.com",
            "password": "Long secure password 123!",
        },
    )
    assert login.status_code == 200
    assert "refresh_token" not in login.json()
    csrf = login.json()["csrf_token"]
    set_cookies = login.headers.get_list("set-cookie")
    assert any("resolvehub_refresh=" in value and "HttpOnly" in value for value in set_cookies)
    assert any("resolvehub_csrf=" in value and "HttpOnly" not in value for value in set_cookies)

    rejected = await client.post(
        "/api/v1/auth/browser/refresh",
        headers={"X-ResolveHub-Client": "browser", "X-CSRF-Token": "wrong-token"},
    )
    assert rejected.status_code == 403
    assert rejected.json()["error"]["code"] == "CSRF_TOKEN_INVALID"

    refreshed = await client.post(
        "/api/v1/auth/browser/refresh",
        headers={"X-ResolveHub-Client": "browser", "X-CSRF-Token": csrf},
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["csrf_token"] != csrf
    access_token = refreshed.json()["access_token"]
    assert "refresh_token" not in refreshed.json()

    logout = await client.post(
        "/api/v1/auth/browser/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout.status_code == 204
    assert client.cookies.get("resolvehub_refresh") is None
    assert client.cookies.get("resolvehub_csrf") is None
    assert (
        await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    ).status_code == 401


async def test_browser_login_requires_non_simple_client_header(client: AsyncClient) -> None:
    await register_and_verify(client, "browser-header@example.com")
    response = await client.post(
        "/api/v1/auth/browser/login",
        json={
            "email": "browser-header@example.com",
            "password": "Long secure password 123!",
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BROWSER_CLIENT_HEADER_REQUIRED"


async def test_registration_does_not_enumerate_email(client: AsyncClient) -> None:
    payload = {
        "email": "same@example.com",
        "password": "Long secure password 123!",
        "display_name": "Same",
    }
    first = await client.post("/api/v1/auth/register", json=payload)
    second = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == second.status_code == 202
    assert first.json()["message"] == second.json()["message"]
    assert first.json()["requires_email_verification"] is True
    assert second.json()["requires_email_verification"] is True
    assert second.json()["verification_token"] is None


@pytest.mark.security
async def test_successful_logins_do_not_consume_failed_attempt_quota(client: AsyncClient) -> None:
    email = f"repeated-login-{uuid4()}@example.com"
    await register_verify_login(client, email)

    for _ in range(6):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Long secure password 123!"},
        )
        assert response.status_code == 200


@pytest.mark.security
async def test_failed_logins_are_rate_limited_and_success_resets_failures(
    client: AsyncClient,
) -> None:
    email = f"limited-login-{uuid4()}@example.com"
    await register_verify_login(client, email)

    for _ in range(4):
        failed = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": "incorrect password"}
        )
        assert failed.status_code == 401

    successful = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Long secure password 123!"},
    )
    assert successful.status_code == 200

    for _ in range(5):
        failed = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": "incorrect password"}
        )
        assert failed.status_code == 401

    limited = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "incorrect password"}
    )
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "RATE_LIMITED"


async def test_session_listing_health_and_duplicate_guards(client: AsyncClient) -> None:
    assert (await client.get("/health/live")).json() == {"status": "ok"}
    readiness = await client.get("/health/ready")
    assert readiness.status_code == 200, readiness.json()
    assert readiness.json()["status"] == "ok"

    tokens = await register_verify_login(client, "account@example.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "account@example.com"
    sessions = await client.get("/api/v1/auth/sessions", headers=headers)
    assert sessions.status_code == 200
    assert len(sessions.json()) == 1

    payload = {"name": "Account Org", "slug": "account-org"}
    organisation = await client.post("/api/v1/organisations", headers=headers, json=payload)
    assert organisation.status_code == 201
    duplicate = await client.post("/api/v1/organisations", headers=headers, json=payload)
    assert duplicate.status_code == 409
    listed = await client.get("/api/v1/organisations", headers=headers)
    assert [item["id"] for item in listed.json()] == [organisation.json()["id"]]

    organisation_id = organisation.json()["id"]
    department_payload = {"name": "Operations"}
    created = await client.post(
        f"/api/v1/organisations/{organisation_id}/departments",
        headers=headers,
        json=department_payload,
    )
    assert created.status_code == 201
    duplicate_department = await client.post(
        f"/api/v1/organisations/{organisation_id}/departments",
        headers=headers,
        json=department_payload,
    )
    assert duplicate_department.status_code == 409
    departments = await client.get(
        f"/api/v1/organisations/{organisation_id}/departments", headers=headers
    )
    assert [item["name"] for item in departments.json()] == ["Operations"]

    assert (await client.post("/api/v1/auth/logout", headers=headers)).status_code == 204
    assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 401


async def test_invalid_authentication_inputs_are_rejected(client: AsyncClient) -> None:
    registration = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "unverified@example.com",
            "password": "Long secure password 123!",
            "display_name": "Unverified",
        },
    )
    assert registration.status_code == 202
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "unverified@example.com", "password": "Long secure password 123!"},
    )
    assert login.status_code == 401
    unknown = await client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@example.com", "password": "Long secure password 123!"},
    )
    assert unknown.status_code == 401
    assert unknown.json()["error"]["code"] == login.json()["error"]["code"]
    assert (
        await client.post("/api/v1/auth/verify-email", json={"token": "x" * 48})
    ).status_code == 400
    assert (
        await client.post("/api/v1/auth/refresh", json={"refresh_token": "x" * 48})
    ).status_code == 401
    assert (await client.get("/api/v1/auth/me")).status_code == 401
