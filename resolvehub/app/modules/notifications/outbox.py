from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from resolvehub.app.modules.notifications.models import OutboxRecord, OutboxStatus


def enqueue_event(
    session: AsyncSession,
    *,
    organisation_id: UUID,
    aggregate_type: str,
    aggregate_id: UUID,
    event_type: str,
    payload: dict[str, Any],
    dedupe_key: str,
) -> OutboxRecord:
    record = OutboxRecord(
        id=uuid4(),
        organisation_id=organisation_id,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload=payload,
        dedupe_key=dedupe_key,
        status=OutboxStatus.PENDING,
        attempts=0,
        available_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    session.add(record)
    return record
