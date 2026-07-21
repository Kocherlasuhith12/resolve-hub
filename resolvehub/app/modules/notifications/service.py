from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import and_, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from resolvehub.app.core.exceptions import AppError
from resolvehub.app.core.pagination import decode_cursor, encode_cursor
from resolvehub.app.modules.identity.models import User
from resolvehub.app.modules.notifications.models import (
    DeliveryAttempt,
    DeliveryStatus,
    Notification,
    OutboxRecord,
    OutboxStatus,
)
from resolvehub.app.modules.notifications.providers import (
    DeterministicEmailProvider,
    EmailMessage,
    EmailProvider,
)
from resolvehub.app.modules.organisations.models import (
    Membership,
    Permission,
    Role,
    role_permissions,
)
from resolvehub.app.modules.organisations.service import require_permission

Publisher = Callable[[str, dict[str, Any]], Awaitable[None]]
logger = structlog.get_logger()


async def list_notifications(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    cursor: str | None,
    limit: int,
) -> tuple[list[Notification], str | None]:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="notification:read",
    )
    statement = select(Notification).where(
        Notification.organisation_id == organisation_id, Notification.user_id == actor_id
    )
    if cursor:
        created_at, item_id = decode_cursor(cursor)
        statement = statement.where(
            or_(
                Notification.created_at < created_at,
                and_(Notification.created_at == created_at, Notification.id < item_id),
            )
        )
    items = list(
        await session.scalars(
            statement.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(
                limit + 1
            )
        )
    )
    next_cursor = None
    if len(items) > limit:
        items = items[:limit]
        next_cursor = encode_cursor(items[-1].created_at, items[-1].id)
    return items, next_cursor


async def mark_notification_read(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    notification_id: UUID,
) -> Notification:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="notification:read",
    )
    item = await session.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.organisation_id == organisation_id,
            Notification.user_id == actor_id,
        )
    )
    if item is None:
        raise AppError("NOTIFICATION_NOT_FOUND", "Notification was not found.", 404)
    item.read_at = item.read_at or datetime.now(UTC)
    await session.commit()
    return item


def _safe_message(record: OutboxRecord) -> tuple[str, str]:
    number = str(record.payload.get("ticket_number", "ticket"))
    labels = {
        "TICKET_CREATED": "Ticket created",
        "AGENT_ASSIGNED": "Ticket assigned",
        "STATUS_CHANGED": "Ticket status changed",
        "COMMENT_ADDED": "New ticket comment",
        "INTERNAL_NOTE_ADDED": "New internal note",
        "ATTACHMENT_METADATA_CREATED": "Ticket attachment added",
        "SLA_WARNING": "SLA warning",
        "SLA_BREACHED": "SLA breached",
    }
    title = labels.get(record.event_type, "Ticket updated")
    return title, f"{number} has a new {record.event_type.casefold().replace('_', ' ')} event."


async def claim_outbox_batch(session: AsyncSession, *, limit: int, now: datetime) -> list[UUID]:
    records = list(
        await session.scalars(
            select(OutboxRecord)
            .where(
                or_(
                    OutboxRecord.status.in_([OutboxStatus.PENDING, OutboxStatus.FAILED]),
                    and_(
                        OutboxRecord.status == OutboxStatus.PROCESSING,
                        OutboxRecord.locked_at < now - timedelta(minutes=5),
                    ),
                ),
                OutboxRecord.available_at <= now,
                OutboxRecord.attempts < 10,
            )
            .order_by(OutboxRecord.created_at)
            .with_for_update(skip_locked=True)
            .limit(limit)
        )
    )
    for record in records:
        record.status = OutboxStatus.PROCESSING
        record.locked_at = now
        record.attempts += 1
    await session.commit()
    return [record.id for record in records]


async def deliver_outbox_record(
    session: AsyncSession,
    *,
    record_id: UUID,
    publisher: Publisher,
    email_provider: EmailProvider,
) -> None:
    record = await session.scalar(
        select(OutboxRecord).where(OutboxRecord.id == record_id).with_for_update()
    )
    if record is None or record.status == OutboxStatus.DELIVERED:
        return
    recipient_ids = {UUID(item) for item in record.payload.get("recipient_ids", [])}
    if recipient_ids:
        recipients_statement = select(Membership.user_id).where(
            Membership.organisation_id == record.organisation_id,
            Membership.user_id.in_(recipient_ids),
            Membership.is_active.is_(True),
        )
        if record.payload.get("visibility") == "staff":
            recipients_statement = (
                recipients_statement.join(Role, Role.id == Membership.role_id)
                .join(role_permissions, role_permissions.c.role_id == Role.id)
                .join(Permission, Permission.id == role_permissions.c.permission_id)
                .where(Permission.code == "internal_note:read")
            )
        active_ids = set(await session.scalars(recipients_statement))
    else:
        active_ids = set()
    title, body = _safe_message(record)
    now = datetime.now(UTC)
    for user_id in active_ids:
        await session.execute(
            insert(Notification)
            .values(
                organisation_id=record.organisation_id,
                user_id=user_id,
                source_outbox_id=record.id,
                kind=record.event_type,
                title=title,
                body=body,
                resource_type=record.aggregate_type,
                resource_id=record.aggregate_id,
                created_at=now,
            )
            .on_conflict_do_nothing(
                index_elements=["organisation_id", "user_id", "source_outbox_id"]
            )
        )
    try:
        users = list(await session.scalars(select(User).where(User.id.in_(active_ids))))
        for user in users:
            provider_reference = await email_provider.send(
                EmailMessage(
                    recipient=user.email,
                    subject=title,
                    text_body=body,
                    idempotency_key=f"{record.id}:email:{user.id}",
                )
            )
            session.add(
                DeliveryAttempt(
                    organisation_id=record.organisation_id,
                    outbox_id=record.id,
                    channel="email",
                    recipient=user.email,
                    attempt_number=record.attempts,
                    status=DeliveryStatus.SENT,
                    provider_reference=provider_reference,
                    created_at=now,
                )
            )
        await publisher(
            f"resolvehub:realtime:{record.organisation_id}",
            {
                "id": str(record.id),
                "type": record.event_type,
                "resource_type": record.aggregate_type,
                "resource_id": str(record.aggregate_id),
                "visibility": record.payload.get("visibility", "public"),
                "recipient_ids": [str(item) for item in active_ids],
                "created_at": record.created_at.isoformat(),
            },
        )
    except Exception as exc:
        record.status = OutboxStatus.FAILED
        record.last_error = type(exc).__name__
        record.available_at = now + timedelta(seconds=min(300, 2**record.attempts))
        await session.commit()
        raise
    record.status = OutboxStatus.DELIVERED
    record.delivered_at = now
    record.locked_at = None
    record.last_error = None
    await session.commit()


async def process_outbox(
    factory: async_sessionmaker[AsyncSession],
    *,
    limit: int,
    publisher: Publisher,
    email_provider: EmailProvider | None = None,
) -> int:
    provider = email_provider or DeterministicEmailProvider()
    async with factory() as session:
        ids = await claim_outbox_batch(session, limit=limit, now=datetime.now(UTC))
    delivered = 0
    for record_id in ids:
        async with factory() as session:
            try:
                await deliver_outbox_record(
                    session,
                    record_id=record_id,
                    publisher=publisher,
                    email_provider=provider,
                )
                delivered += 1
            except Exception as exc:
                await logger.awarning(
                    "outbox_delivery_failed", record_id=str(record_id), error=type(exc).__name__
                )
                continue
    return delivered
