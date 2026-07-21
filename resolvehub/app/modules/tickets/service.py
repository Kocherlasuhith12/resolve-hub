import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import PurePath
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from resolvehub.app.core.exceptions import AppError
from resolvehub.app.core.pagination import decode_cursor, encode_cursor
from resolvehub.app.modules.attachments.models import Attachment
from resolvehub.app.modules.comments.models import TicketComment
from resolvehub.app.modules.identity.models import User
from resolvehub.app.modules.notifications.outbox import enqueue_event
from resolvehub.app.modules.organisations.models import (
    Membership,
    Permission,
    Role,
    role_permissions,
)
from resolvehub.app.modules.organisations.service import (
    membership_has_permission,
    require_permission,
)
from resolvehub.app.modules.service_catalogue.models import ServiceCategory
from resolvehub.app.modules.tickets.enums import (
    ActorType,
    CommentKind,
    MalwareScanStatus,
    SlaState,
    TicketPriority,
    TicketSource,
    TicketStatus,
)
from resolvehub.app.modules.tickets.models import IdempotencyRecord, Ticket, TicketEvent
from resolvehub.app.modules.tickets.state_machine import validate_transition

ALLOWED_ATTACHMENT_TYPES = {
    "application/pdf": {".pdf"},
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "text/plain": {".txt"},
}


def request_fingerprint(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def generate_ticket_number() -> str:
    return f"RH-{uuid4().hex[:12].upper()}"


def add_event(
    session: AsyncSession,
    *,
    ticket: Ticket,
    actor_id: UUID | None,
    event_type: str,
    correlation_id: UUID,
    previous_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
    event_metadata: dict[str, Any] | None = None,
) -> None:
    event = TicketEvent(
        id=uuid4(),
        organisation_id=ticket.organisation_id,
        ticket_id=ticket.id,
        actor_id=actor_id,
        actor_type=ActorType.HUMAN if actor_id else ActorType.SYSTEM,
        event_type=event_type,
        previous_values=previous_values,
        new_values=new_values,
        event_metadata=event_metadata or {},
        correlation_id=correlation_id,
        created_at=datetime.now(UTC),
    )
    session.add(event)
    recipients = {ticket.requester_id}
    if ticket.assigned_agent_id:
        recipients.add(ticket.assigned_agent_id)
    enqueue_event(
        session,
        organisation_id=ticket.organisation_id,
        aggregate_type="ticket",
        aggregate_id=ticket.id,
        event_type=event_type,
        payload={
            "ticket_number": ticket.ticket_number,
            "recipient_ids": [str(item) for item in sorted(recipients, key=str)],
            "visibility": "staff" if event_type == "INTERNAL_NOTE_ADDED" else "public",
        },
        dedupe_key=f"ticket-event:{event.id}",
    )


async def get_accessible_ticket(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    ticket_id: UUID,
    for_update: bool = False,
) -> tuple[Ticket, Membership]:
    membership = await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="ticket:read",
    )
    statement = select(Ticket).where(
        Ticket.id == ticket_id, Ticket.organisation_id == organisation_id
    )
    if not membership_has_permission(membership, "ticket:read_all"):
        statement = statement.where(Ticket.requester_id == actor_id)
    if for_update:
        statement = statement.with_for_update()
    ticket = await session.scalar(statement)
    if ticket is None:
        raise AppError("TICKET_NOT_FOUND", "Ticket was not found.", 404)
    return ticket, membership


async def create_ticket(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    category_id: UUID,
    title: str,
    description: str,
    priority: TicketPriority | None,
    source: TicketSource,
    idempotency_key: str,
    correlation_id: UUID,
) -> tuple[Ticket, bool]:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="ticket:create",
    )
    payload = {
        "category_id": str(category_id),
        "title": title,
        "description": description,
        "priority": priority,
        "source": source,
    }
    fingerprint = request_fingerprint(payload)
    existing_record = await session.scalar(
        select(IdempotencyRecord).where(
            IdempotencyRecord.organisation_id == organisation_id,
            IdempotencyRecord.actor_id == actor_id,
            IdempotencyRecord.operation == "ticket:create",
            IdempotencyRecord.key == idempotency_key,
            IdempotencyRecord.expires_at > datetime.now(UTC),
        )
    )
    if existing_record:
        if existing_record.request_fingerprint != fingerprint:
            raise AppError(
                "IDEMPOTENCY_KEY_REUSED",
                "Idempotency key was already used with a different request.",
                409,
            )
        existing_ticket = await session.get(
            Ticket, UUID(existing_record.response_body["ticket_id"])
        )
        if existing_ticket is None:
            raise AppError("IDEMPOTENCY_RECORD_INVALID", "Stored response is unavailable.", 500)
        return existing_ticket, True
    category = await session.scalar(
        select(ServiceCategory).where(
            ServiceCategory.id == category_id,
            ServiceCategory.organisation_id == organisation_id,
            ServiceCategory.is_active.is_(True),
        )
    )
    if category is None:
        raise AppError("CATEGORY_NOT_FOUND", "Category was not found.", 404)
    now = datetime.now(UTC)
    ticket = Ticket(
        ticket_number=generate_ticket_number(),
        organisation_id=organisation_id,
        requester_id=actor_id,
        department_id=category.department_id,
        category_id=category.id,
        title=title,
        description=description,
        priority=priority or category.default_priority,
        status=TicketStatus.SUBMITTED,
        source=source,
        sla_state=SlaState.NOT_STARTED,
        version=1,
    )
    session.add(ticket)
    await session.flush()
    from resolvehub.app.modules.sla.service import start_sla_for_ticket

    await start_sla_for_ticket(session, ticket, now)
    add_event(
        session,
        ticket=ticket,
        actor_id=actor_id,
        event_type="TICKET_CREATED",
        correlation_id=correlation_id,
        new_values={"status": ticket.status, "priority": ticket.priority},
    )
    session.add(
        IdempotencyRecord(
            organisation_id=organisation_id,
            actor_id=actor_id,
            operation="ticket:create",
            key=idempotency_key,
            request_fingerprint=fingerprint,
            response_status=201,
            response_body={"ticket_id": str(ticket.id)},
            created_at=now,
            expires_at=now + timedelta(hours=24),
        )
    )
    await session.commit()
    await session.refresh(ticket)
    return ticket, False


async def list_tickets(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    status: TicketStatus | None,
    priority: TicketPriority | None,
    department_id: UUID | None,
    assignee_id: UUID | None,
    category_id: UUID | None,
    cursor: str | None,
    limit: int,
) -> tuple[list[Ticket], str | None]:
    membership = await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="ticket:read",
    )
    statement = select(Ticket).where(Ticket.organisation_id == organisation_id)
    if not membership_has_permission(membership, "ticket:read_all"):
        statement = statement.where(Ticket.requester_id == actor_id)
    if status:
        statement = statement.where(Ticket.status == status)
    if priority:
        statement = statement.where(Ticket.priority == priority)
    if department_id:
        statement = statement.where(Ticket.department_id == department_id)
    if assignee_id:
        statement = statement.where(Ticket.assigned_agent_id == assignee_id)
    if category_id:
        statement = statement.where(Ticket.category_id == category_id)
    if cursor:
        created_at, item_id = decode_cursor(cursor)
        statement = statement.where(
            or_(
                Ticket.created_at < created_at,
                and_(Ticket.created_at == created_at, Ticket.id < item_id),
            )
        )
    result = list(
        await session.scalars(
            statement.order_by(Ticket.created_at.desc(), Ticket.id.desc()).limit(limit + 1)
        )
    )
    next_cursor = None
    if len(result) > limit:
        result = result[:limit]
        next_cursor = encode_cursor(result[-1].created_at, result[-1].id)
    return result, next_cursor


async def assign_ticket(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    ticket_id: UUID,
    assigned_agent_id: UUID,
    expected_version: int,
    correlation_id: UUID,
) -> Ticket:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="ticket:assign",
    )
    ticket, _ = await get_accessible_ticket(
        session,
        actor_id=actor_id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
        for_update=True,
    )
    if ticket.version != expected_version:
        raise AppError("TICKET_VERSION_CONFLICT", "Ticket was modified by another request.", 409)
    target = await session.scalar(
        select(Membership)
        .options(selectinload(Membership.role).selectinload(Role.permissions))
        .where(
            Membership.organisation_id == organisation_id,
            Membership.user_id == assigned_agent_id,
            Membership.is_active.is_(True),
        )
    )
    if target is None or not membership_has_permission(target, "ticket:read_all"):
        raise AppError("ASSIGNEE_INVALID", "Assignee is not an active ticket agent.", 422)
    previous = ticket.assigned_agent_id
    ticket.assigned_agent_id = assigned_agent_id
    ticket.version += 1
    add_event(
        session,
        ticket=ticket,
        actor_id=actor_id,
        event_type="AGENT_ASSIGNED",
        correlation_id=correlation_id,
        previous_values={"assigned_agent_id": str(previous) if previous else None},
        new_values={"assigned_agent_id": str(assigned_agent_id)},
    )
    await session.commit()
    await session.refresh(ticket)
    return ticket


async def list_assignment_candidates(
    session: AsyncSession, *, actor_id: UUID, organisation_id: UUID
) -> list[User]:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="ticket:assign",
    )
    result = await session.scalars(
        select(User)
        .join(Membership, Membership.user_id == User.id)
        .join(Role, Role.id == Membership.role_id)
        .join(role_permissions, role_permissions.c.role_id == Role.id)
        .join(Permission, Permission.id == role_permissions.c.permission_id)
        .where(
            Membership.organisation_id == organisation_id,
            Membership.is_active.is_(True),
            User.is_active.is_(True),
            Permission.code == "ticket:read_all",
        )
        .order_by(User.display_name, User.id)
        .limit(200)
    )
    return list(result)


async def transition_ticket(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    ticket_id: UUID,
    requested_status: TicketStatus,
    expected_version: int,
    reason: str | None,
    correlation_id: UUID,
) -> Ticket:
    permission = {
        TicketStatus.RESOLVED: "ticket:resolve",
        TicketStatus.REOPENED: "ticket:reopen",
        TicketStatus.ESCALATED: "ticket:escalate",
    }.get(requested_status, "ticket:transition")
    await require_permission(
        session, user_id=actor_id, organisation_id=organisation_id, permission=permission
    )
    ticket, _ = await get_accessible_ticket(
        session,
        actor_id=actor_id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
        for_update=True,
    )
    if ticket.version != expected_version:
        raise AppError("TICKET_VERSION_CONFLICT", "Ticket was modified by another request.", 409)
    decision = validate_transition(
        current=ticket.status,
        requested=requested_status,
        reason=reason,
        assigned=ticket.assigned_agent_id is not None,
    )
    ticket.status = decision.current
    ticket.version += 1
    now = datetime.now(UTC)
    if requested_status == TicketStatus.RESOLVED:
        ticket.resolved_at = now
    elif requested_status == TicketStatus.CLOSED:
        ticket.closed_at = now
    elif requested_status == TicketStatus.REOPENED:
        ticket.resolved_at = None
        ticket.closed_at = None
    from resolvehub.app.modules.sla.service import update_sla_for_transition

    await update_sla_for_transition(session, ticket, decision.previous, now)
    add_event(
        session,
        ticket=ticket,
        actor_id=actor_id,
        event_type="STATUS_CHANGED",
        correlation_id=correlation_id,
        previous_values={"status": decision.previous},
        new_values={"status": decision.current},
        event_metadata={"reason": reason} if reason else {},
    )
    await session.commit()
    await session.refresh(ticket)
    return ticket


async def add_comment(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    ticket_id: UUID,
    kind: CommentKind,
    body: str,
    correlation_id: UUID,
) -> TicketComment:
    ticket, _ = await get_accessible_ticket(
        session,
        actor_id=actor_id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
    )
    permission = "internal_note:create" if kind == CommentKind.INTERNAL else "comment:create"
    await require_permission(
        session, user_id=actor_id, organisation_id=organisation_id, permission=permission
    )
    comment = TicketComment(
        organisation_id=organisation_id,
        ticket_id=ticket_id,
        author_id=actor_id,
        kind=kind,
        body=body,
        created_at=datetime.now(UTC),
    )
    session.add(comment)
    await session.flush()
    add_event(
        session,
        ticket=ticket,
        actor_id=actor_id,
        event_type="INTERNAL_NOTE_ADDED" if kind == CommentKind.INTERNAL else "COMMENT_ADDED",
        correlation_id=correlation_id,
        new_values={"comment_id": str(comment.id), "kind": kind},
    )
    await session.commit()
    return comment


async def list_comments(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    ticket_id: UUID,
    cursor: str | None,
    limit: int,
) -> tuple[list[TicketComment], str | None]:
    _, membership = await get_accessible_ticket(
        session,
        actor_id=actor_id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
    )
    statement = select(TicketComment).where(
        TicketComment.organisation_id == organisation_id,
        TicketComment.ticket_id == ticket_id,
    )
    if not membership_has_permission(membership, "internal_note:read"):
        statement = statement.where(TicketComment.kind == CommentKind.PUBLIC)
    if cursor:
        created_at, item_id = decode_cursor(cursor)
        statement = statement.where(
            or_(
                TicketComment.created_at < created_at,
                and_(TicketComment.created_at == created_at, TicketComment.id < item_id),
            )
        )
    result = list(
        await session.scalars(
            statement.order_by(TicketComment.created_at.desc(), TicketComment.id.desc()).limit(
                limit + 1
            )
        )
    )
    next_cursor = None
    if len(result) > limit:
        result = result[:limit]
        next_cursor = encode_cursor(result[-1].created_at, result[-1].id)
    return result, next_cursor


async def list_events(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    ticket_id: UUID,
    cursor: str | None,
    limit: int,
) -> tuple[list[TicketEvent], str | None]:
    _, membership = await get_accessible_ticket(
        session,
        actor_id=actor_id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
    )
    statement = select(TicketEvent).where(
        TicketEvent.organisation_id == organisation_id, TicketEvent.ticket_id == ticket_id
    )
    if not membership_has_permission(membership, "internal_note:read"):
        statement = statement.where(TicketEvent.event_type != "INTERNAL_NOTE_ADDED")
    if cursor:
        created_at, item_id = decode_cursor(cursor)
        statement = statement.where(
            or_(
                TicketEvent.created_at < created_at,
                and_(TicketEvent.created_at == created_at, TicketEvent.id < item_id),
            )
        )
    result = list(
        await session.scalars(
            statement.order_by(TicketEvent.created_at.desc(), TicketEvent.id.desc()).limit(
                limit + 1
            )
        )
    )
    next_cursor = None
    if len(result) > limit:
        result = result[:limit]
        next_cursor = encode_cursor(result[-1].created_at, result[-1].id)
    return result, next_cursor


async def create_attachment_metadata(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    ticket_id: UUID,
    filename: str,
    content_type: str,
    size_bytes: int,
    correlation_id: UUID,
) -> Attachment:
    ticket, _ = await get_accessible_ticket(
        session,
        actor_id=actor_id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
    )
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="attachment:create",
    )
    safe_name = PurePath(filename).name
    extension = PurePath(safe_name).suffix.casefold()
    if safe_name != filename or content_type not in ALLOWED_ATTACHMENT_TYPES:
        raise AppError("ATTACHMENT_TYPE_FORBIDDEN", "Attachment type is not allowed.", 422)
    if extension not in ALLOWED_ATTACHMENT_TYPES[content_type]:
        raise AppError("ATTACHMENT_TYPE_MISMATCH", "Filename and content type do not match.", 422)
    attachment_id = uuid4()
    attachment = Attachment(
        id=attachment_id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
        uploaded_by_id=actor_id,
        original_filename=safe_name,
        storage_key=f"organisations/{organisation_id}/tickets/{ticket_id}/{attachment_id}",
        content_type=content_type,
        size_bytes=size_bytes,
        upload_completed=False,
        scan_status=MalwareScanStatus.PENDING,
        created_at=datetime.now(UTC),
    )
    session.add(attachment)
    add_event(
        session,
        ticket=ticket,
        actor_id=actor_id,
        event_type="ATTACHMENT_METADATA_CREATED",
        correlation_id=correlation_id,
        new_values={"attachment_id": str(attachment.id), "content_type": content_type},
    )
    await session.commit()
    return attachment
