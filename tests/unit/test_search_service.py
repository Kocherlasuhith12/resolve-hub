from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from resolvehub.app.core.pagination import encode_cursor
from resolvehub.app.modules.search import service
from resolvehub.app.modules.tickets.enums import SlaState, TicketPriority, TicketStatus
from resolvehub.app.modules.tickets.models import Ticket


def search_arguments() -> dict[str, Any]:
    return {
        "actor_id": uuid4(),
        "organisation_id": uuid4(),
        "query": "network outage",
        "status": None,
        "priority": None,
        "department_id": None,
        "assignee_id": None,
        "category_id": None,
        "requester_id": None,
        "sla_state": None,
        "created_from": None,
        "created_to": None,
        "updated_from": None,
        "updated_to": None,
        "cursor": None,
        "limit": 50,
    }


@pytest.mark.asyncio
async def test_search_builds_all_filters_for_requester(monkeypatch: pytest.MonkeyPatch) -> None:
    membership = object()
    monkeypatch.setattr(service, "require_permission", AsyncMock(return_value=membership))
    monkeypatch.setattr(service, "membership_has_permission", lambda *_: False)
    fake_session = SimpleNamespace(scalars=AsyncMock(return_value=[]))
    now = datetime.now(UTC)
    arguments = search_arguments()
    arguments.update(
        status=TicketStatus.SUBMITTED,
        priority=TicketPriority.HIGH,
        department_id=uuid4(),
        assignee_id=uuid4(),
        category_id=uuid4(),
        requester_id=uuid4(),
        sla_state=SlaState.ACTIVE,
        created_from=now,
        created_to=now,
        updated_from=now,
        updated_to=now,
        cursor=encode_cursor(now, uuid4()),
    )

    items, next_cursor = await service.search_tickets(cast(AsyncSession, fake_session), **arguments)

    assert items == []
    assert next_cursor is None
    fake_session.scalars.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_encodes_next_cursor_for_staff(monkeypatch: pytest.MonkeyPatch) -> None:
    membership = object()
    monkeypatch.setattr(service, "require_permission", AsyncMock(return_value=membership))
    monkeypatch.setattr(service, "membership_has_permission", lambda *_: True)
    now = datetime.now(UTC)
    first = cast(Ticket, SimpleNamespace(id=uuid4(), created_at=now))
    second = cast(Ticket, SimpleNamespace(id=uuid4(), created_at=now))
    fake_session = SimpleNamespace(scalars=AsyncMock(return_value=[first, second]))
    arguments = search_arguments()
    arguments["limit"] = 1

    items, next_cursor = await service.search_tickets(cast(AsyncSession, fake_session), **arguments)

    assert items == [first]
    assert next_cursor == encode_cursor(first.created_at, first.id)
