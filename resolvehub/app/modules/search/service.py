from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from resolvehub.app.core.pagination import decode_cursor, encode_cursor
from resolvehub.app.modules.comments.models import TicketComment
from resolvehub.app.modules.identity.models import User
from resolvehub.app.modules.organisations.service import (
    membership_has_permission,
    require_permission,
)
from resolvehub.app.modules.service_catalogue.models import ServiceCategory
from resolvehub.app.modules.tickets.enums import (
    CommentKind,
    SlaState,
    TicketPriority,
    TicketStatus,
)
from resolvehub.app.modules.tickets.models import Ticket


async def search_tickets(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    query: str,
    status: TicketStatus | None,
    priority: TicketPriority | None,
    department_id: UUID | None,
    assignee_id: UUID | None,
    category_id: UUID | None,
    requester_id: UUID | None,
    sla_state: SlaState | None,
    created_from: datetime | None,
    created_to: datetime | None,
    updated_from: datetime | None,
    updated_to: datetime | None,
    cursor: str | None,
    limit: int,
) -> tuple[list[Ticket], str | None]:
    membership = await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="ticket:read",
    )
    can_read_all = membership_has_permission(membership, "ticket:read_all")
    can_read_internal = membership_has_permission(membership, "internal_note:read")
    tsquery = func.websearch_to_tsquery("english", query)

    comment_match = select(TicketComment.id).where(
        TicketComment.organisation_id == organisation_id,
        TicketComment.ticket_id == Ticket.id,
        TicketComment.search_vector.op("@@")(tsquery),
    )
    if not can_read_internal:
        comment_match = comment_match.where(TicketComment.kind == CommentKind.PUBLIC)

    statement = (
        select(Ticket)
        .join(ServiceCategory, ServiceCategory.id == Ticket.category_id)
        .join(User, User.id == Ticket.requester_id)
        .where(
            Ticket.organisation_id == organisation_id,
            or_(
                Ticket.search_vector.op("@@")(tsquery),
                ServiceCategory.search_vector.op("@@")(tsquery),
                User.display_name_search_vector.op("@@")(tsquery),
                comment_match.exists(),
            ),
        )
    )
    if not can_read_all:
        statement = statement.where(Ticket.requester_id == actor_id)
    if status is not None:
        statement = statement.where(Ticket.status == status)
    if priority is not None:
        statement = statement.where(Ticket.priority == priority)
    if department_id is not None:
        statement = statement.where(Ticket.department_id == department_id)
    if assignee_id is not None:
        statement = statement.where(Ticket.assigned_agent_id == assignee_id)
    if category_id is not None:
        statement = statement.where(Ticket.category_id == category_id)
    if requester_id is not None:
        statement = statement.where(Ticket.requester_id == requester_id)
    if sla_state is not None:
        statement = statement.where(Ticket.sla_state == sla_state)
    if created_from is not None:
        statement = statement.where(Ticket.created_at >= created_from)
    if created_to is not None:
        statement = statement.where(Ticket.created_at <= created_to)
    if updated_from is not None:
        statement = statement.where(Ticket.updated_at >= updated_from)
    if updated_to is not None:
        statement = statement.where(Ticket.updated_at <= updated_to)
    if cursor is not None:
        created_at, item_id = decode_cursor(cursor)
        statement = statement.where(
            or_(
                Ticket.created_at < created_at,
                and_(Ticket.created_at == created_at, Ticket.id < item_id),
            )
        )

    results = list(
        await session.scalars(
            statement.order_by(Ticket.created_at.desc(), Ticket.id.desc()).limit(limit + 1)
        )
    )
    next_cursor = None
    if len(results) > limit:
        results = results[:limit]
        next_cursor = encode_cursor(results[-1].created_at, results[-1].id)
    return results, next_cursor
