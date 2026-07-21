import os
from datetime import date, timedelta
from typing import Any, cast
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from resolvehub.app.modules.notifications.models import DeliveryAttempt, Notification, OutboxRecord
from resolvehub.app.modules.notifications.service import process_outbox
from resolvehub.app.modules.sla.models import TicketSla
from resolvehub.app.modules.tickets.enums import SlaState
from resolvehub.app.modules.tickets.models import TicketEvent
from resolvehub.app.temporal.activities import record_sla_event_in_session

pytestmark = pytest.mark.integration


async def register_verify_login(client: AsyncClient, email: str) -> dict[str, Any]:
    registration = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Long secure password 123!", "display_name": email},
    )
    token = registration.json()["verification_token"]
    assert (
        await client.post("/api/v1/auth/verify-email", json={"token": token})
    ).status_code == 204
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Long secure password 123!"}
    )
    return cast(dict[str, Any], login.json())


def auth(tokens: dict[str, Any]) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.mark.security
async def test_sla_outbox_notifications_and_tenant_isolation(client: AsyncClient) -> None:
    owner = await register_verify_login(client, "phase3-owner@example.com")
    outsider = await register_verify_login(client, "phase3-outsider@example.com")
    owner_headers, outsider_headers = auth(owner), auth(outsider)
    organisation = await client.post(
        "/api/v1/organisations",
        headers=owner_headers,
        json={"name": "Workflow Operations", "slug": "workflow-operations"},
    )
    organisation_id = organisation.json()["id"]
    outsider_org = await client.post(
        "/api/v1/organisations",
        headers=outsider_headers,
        json={"name": "Other Workflow Org", "slug": "other-workflow-org"},
    )
    assert outsider_org.status_code == 201
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
            "name": "Network",
            "default_priority": "HIGH",
        },
    )
    calendar = await client.post(
        f"/api/v1/organisations/{organisation_id}/sla/calendars",
        headers=owner_headers,
        json={
            "name": "India weekdays",
            "timezone": "Asia/Kolkata",
            "weekly_hours": {str(day): [["09:00", "17:00"]] for day in range(5)},
        },
    )
    assert calendar.status_code == 201
    duplicate_calendar = await client.post(
        f"/api/v1/organisations/{organisation_id}/sla/calendars",
        headers=owner_headers,
        json={
            "name": "India weekdays",
            "timezone": "Asia/Kolkata",
            "weekly_hours": {str(day): [["09:00", "17:00"]] for day in range(5)},
        },
    )
    assert duplicate_calendar.status_code == 409
    holiday = await client.post(
        f"/api/v1/organisations/{organisation_id}/sla/calendars/{calendar.json()['id']}/holidays",
        headers=owner_headers,
        json={"holiday_date": str(date.today() + timedelta(days=30)), "name": "Operations day"},
    )
    assert holiday.status_code == 204
    missing_holiday_calendar = await client.post(
        f"/api/v1/organisations/{organisation_id}/sla/calendars/{UUID(int=0)}/holidays",
        headers=owner_headers,
        json={"holiday_date": "2030-01-01", "name": "Missing calendar"},
    )
    assert missing_holiday_calendar.status_code == 404
    listed_calendars = await client.get(
        f"/api/v1/organisations/{organisation_id}/sla/calendars", headers=owner_headers
    )
    assert len(listed_calendars.json()) == 1
    denied_calendar = await client.get(
        f"/api/v1/organisations/{organisation_id}/sla/calendars", headers=outsider_headers
    )
    assert denied_calendar.status_code == 403
    policy = await client.post(
        f"/api/v1/organisations/{organisation_id}/sla/policies",
        headers=owner_headers,
        json={
            "category_id": category.json()["id"],
            "calendar_id": calendar.json()["id"],
            "priority": "HIGH",
            "first_response_minutes": 60,
            "resolution_minutes": 240,
            "warning_percent": 75,
        },
    )
    assert policy.status_code == 201
    invalid_target = await client.post(
        f"/api/v1/organisations/{organisation_id}/sla/policies",
        headers=owner_headers,
        json={
            "category_id": category.json()["id"],
            "calendar_id": calendar.json()["id"],
            "priority": "LOW",
            "first_response_minutes": 120,
            "resolution_minutes": 60,
        },
    )
    assert invalid_target.status_code == 422
    duplicate_policy = await client.post(
        f"/api/v1/organisations/{organisation_id}/sla/policies",
        headers=owner_headers,
        json={
            "category_id": category.json()["id"],
            "calendar_id": calendar.json()["id"],
            "priority": "HIGH",
            "first_response_minutes": 60,
            "resolution_minutes": 240,
        },
    )
    assert duplicate_policy.status_code == 409
    listed_policies = await client.get(
        f"/api/v1/organisations/{organisation_id}/sla/policies", headers=owner_headers
    )
    assert len(listed_policies.json()) == 1
    created = await client.post(
        f"/api/v1/organisations/{organisation_id}/tickets",
        headers={**owner_headers, "Idempotency-Key": "phase3-ticket-001"},
        json={
            "category_id": category.json()["id"],
            "title": "Core switch is unreachable",
            "description": "Sensitive diagnostics must never enter realtime payloads.",
        },
    )
    assert created.status_code == 201
    assert created.json()["sla_state"] == "ACTIVE"
    assert created.json()["first_response_deadline"] is not None
    assert created.json()["resolution_deadline"] is not None

    database_url = os.environ["RH_TEST_DATABASE_URL"]
    engine = create_async_engine(database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        records = list(
            await session.scalars(
                select(OutboxRecord).where(OutboxRecord.organisation_id == organisation_id)
            )
        )
        assert len(records) == 1
        assert "description" not in records[0].payload
        assert "Sensitive diagnostics" not in str(records[0].payload)

    published: list[tuple[str, dict[str, Any]]] = []

    async def fake_publish(channel: str, payload: dict[str, Any]) -> None:
        published.append((channel, payload))

    assert await process_outbox(factory, limit=10, publisher=fake_publish) == 1
    assert await process_outbox(factory, limit=10, publisher=fake_publish) == 0
    assert published[0][0] == f"resolvehub:realtime:{organisation_id}"
    async with factory() as session:
        notifications = list(await session.scalars(select(Notification)))
        assert len(notifications) == 1
        attempts = list(await session.scalars(select(DeliveryAttempt)))
        assert len(attempts) == 1
        assert attempts[0].provider_reference is not None
        assert attempts[0].provider_reference.startswith("deterministic:")

    async with factory() as session:
        await record_sla_event_in_session(
            session,
            organisation_id=UUID(organisation_id),
            ticket_id=UUID(created.json()["id"]),
            event_type="SLA_WARNING",
        )
    async with factory() as session:
        await record_sla_event_in_session(
            session,
            organisation_id=UUID(organisation_id),
            ticket_id=UUID(created.json()["id"]),
            event_type="SLA_WARNING",
        )
    async with factory() as session:
        warning_events = list(
            await session.scalars(
                select(TicketEvent).where(
                    TicketEvent.organisation_id == UUID(organisation_id),
                    TicketEvent.event_type == "SLA_WARNING",
                )
            )
        )
        assert len(warning_events) == 1
    assert await process_outbox(factory, limit=10, publisher=fake_publish) == 1

    owner_id = (await client.get("/api/v1/auth/me", headers=owner_headers)).json()["id"]
    assigned = await client.post(
        f"/api/v1/organisations/{organisation_id}/tickets/{created.json()['id']}/assignment",
        headers=owner_headers,
        json={"assigned_agent_id": owner_id, "version": 1},
    )
    version = assigned.json()["version"]
    for next_status in ("TRIAGED", "ASSIGNED", "IN_PROGRESS", "WAITING_FOR_REQUESTER"):
        transitioned = await client.post(
            f"/api/v1/organisations/{organisation_id}/tickets/{created.json()['id']}/transitions",
            headers=owner_headers,
            json={"status": next_status, "version": version},
        )
        assert transitioned.status_code == 200
        version = transitioned.json()["version"]
    async with factory() as session:
        execution = await session.scalar(
            select(TicketSla).where(TicketSla.ticket_id == UUID(created.json()["id"]))
        )
        assert execution is not None and execution.state == SlaState.PAUSED
    resumed = await client.post(
        f"/api/v1/organisations/{organisation_id}/tickets/{created.json()['id']}/transitions",
        headers=owner_headers,
        json={"status": "IN_PROGRESS", "version": version},
    )
    assert resumed.status_code == 200
    resolved = await client.post(
        f"/api/v1/organisations/{organisation_id}/tickets/{created.json()['id']}/transitions",
        headers=owner_headers,
        json={"status": "RESOLVED", "version": resumed.json()["version"]},
    )
    assert resolved.status_code == 200
    async with factory() as session:
        execution = await session.scalar(
            select(TicketSla).where(TicketSla.ticket_id == UUID(created.json()["id"]))
        )
        assert execution is not None and execution.state == SlaState.COMPLETED

    listed = await client.get(
        f"/api/v1/organisations/{organisation_id}/notifications", headers=owner_headers
    )
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 2
    notification_id = listed.json()["items"][0]["id"]
    read = await client.post(
        f"/api/v1/organisations/{organisation_id}/notifications/{notification_id}/read",
        headers=owner_headers,
    )
    assert read.status_code == 200
    assert read.json()["read_at"] is not None
    cross_tenant_read = await client.get(
        f"/api/v1/organisations/{organisation_id}/notifications", headers=outsider_headers
    )
    assert cross_tenant_read.status_code == 403
    missing_notification = await client.post(
        f"/api/v1/organisations/{organisation_id}/notifications/{UUID(int=0)}/read",
        headers=owner_headers,
    )
    assert missing_notification.status_code == 404

    async def failing_publish(channel: str, payload: dict[str, Any]) -> None:
        del channel, payload
        raise RuntimeError("deterministic publish failure")

    assert await process_outbox(factory, limit=20, publisher=failing_publish) == 0
    await engine.dispose()
