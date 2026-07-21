from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from resolvehub.app.modules.sla.calculator import add_business_minutes, validate_weekly_hours
from resolvehub.app.realtime.routes import bearer_from_protocol, organisation_events
from resolvehub.app.temporal.workflows import TicketSlaWorkflow


def test_business_minutes_skip_weekend_and_holiday() -> None:
    hours = {str(day): [["09:00", "17:00"]] for day in range(5)}
    start = datetime(2026, 7, 16, 15, 0, tzinfo=UTC)  # Thursday
    deadline = add_business_minutes(
        start,
        240,
        timezone="UTC",
        weekly_hours=hours,
        holidays={date(2026, 7, 17)},
    )
    assert deadline == datetime(2026, 7, 20, 11, 0, tzinfo=UTC)


def test_business_minutes_respect_local_timezone() -> None:
    deadline = add_business_minutes(
        datetime(2026, 7, 16, 3, 0, tzinfo=UTC),
        60,
        timezone="Asia/Kolkata",
        weekly_hours={"3": [["09:00", "17:00"]]},
    )
    assert deadline == datetime(2026, 7, 16, 4, 30, tzinfo=UTC)


def test_invalid_overlapping_calendar_is_rejected() -> None:
    with pytest.raises(ValueError, match="non-overlapping"):
        validate_weekly_hours({"0": [["09:00", "12:00"], ["11:00", "13:00"]]})


def test_websocket_credentials_require_exact_bearer_protocol_shape() -> None:
    assert bearer_from_protocol("bearer, signed.jwt.value") == "signed.jwt.value"
    assert bearer_from_protocol("bearer") is None
    assert bearer_from_protocol("other, token") is None
    assert bearer_from_protocol(None) is None


class FakeWebSocket:
    def __init__(self, protocol: str | None) -> None:
        self.headers = {"sec-websocket-protocol": protocol} if protocol else {}
        self.closed: tuple[int, str] | None = None

    async def close(self, *, code: int, reason: str) -> None:
        self.closed = (code, reason)


@pytest.mark.asyncio
async def test_websocket_rejects_missing_and_invalid_credentials() -> None:
    missing = FakeWebSocket(None)
    await organisation_events(missing, uuid4())  # type: ignore[arg-type]
    assert missing.closed == (1008, "Authentication required")
    invalid = FakeWebSocket("bearer, definitely-not-a-jwt")
    await organisation_events(invalid, uuid4())  # type: ignore[arg-type]
    assert invalid.closed == (1008, "Invalid credentials")


def test_temporal_workflow_initial_state_is_deterministic() -> None:
    state = TicketSlaWorkflow()
    assert state.paused is False
    assert state.completed is False
    assert state.pause_started is None
