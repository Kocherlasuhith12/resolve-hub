import csv
import io
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from resolvehub.app.modules.analytics.schemas import AnalyticsSummaryResponse
from resolvehub.app.modules.organisations.service import require_permission
from resolvehub.app.modules.service_catalogue.models import ServiceCategory
from resolvehub.app.modules.tickets.enums import SlaState, TicketStatus
from resolvehub.app.modules.tickets.models import Ticket


async def get_analytics_summary(
    session: AsyncSession, *, actor_id: UUID, organisation_id: UUID
) -> AnalyticsSummaryResponse:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="analytics:read",
    )

    # Count by status
    total_tickets = (
        await session.scalar(
            select(func.count(Ticket.id)).where(Ticket.organisation_id == organisation_id)
        )
        or 0
    )

    open_tickets = (
        await session.scalar(
            select(func.count(Ticket.id)).where(
                Ticket.organisation_id == organisation_id,
                Ticket.status.in_([TicketStatus.SUBMITTED, TicketStatus.DRAFT]),
            )
        )
        or 0
    )

    in_progress_tickets = (
        await session.scalar(
            select(func.count(Ticket.id)).where(
                Ticket.organisation_id == organisation_id,
                Ticket.status.in_(
                    [
                        TicketStatus.TRIAGED,
                        TicketStatus.ASSIGNED,
                        TicketStatus.IN_PROGRESS,
                        TicketStatus.WAITING_FOR_REQUESTER,
                        TicketStatus.ESCALATED,
                        TicketStatus.REOPENED,
                    ]
                ),
            )
        )
        or 0
    )

    resolved_tickets = (
        await session.scalar(
            select(func.count(Ticket.id)).where(
                Ticket.organisation_id == organisation_id,
                Ticket.status == TicketStatus.RESOLVED,
            )
        )
        or 0
    )

    closed_tickets = (
        await session.scalar(
            select(func.count(Ticket.id)).where(
                Ticket.organisation_id == organisation_id,
                Ticket.status.in_([TicketStatus.CLOSED, TicketStatus.CANCELLED]),
            )
        )
        or 0
    )

    # Count by priority
    priority_rows = await session.execute(
        select(Ticket.priority, func.count(Ticket.id))
        .where(Ticket.organisation_id == organisation_id)
        .group_by(Ticket.priority)
    )
    tickets_by_priority = {
        str(row[0].value if hasattr(row[0], "value") else row[0]): row[1] for row in priority_rows
    }

    # Count by category
    category_rows = await session.execute(
        select(ServiceCategory.name, func.count(Ticket.id))
        .join(ServiceCategory, ServiceCategory.id == Ticket.category_id)
        .where(Ticket.organisation_id == organisation_id)
        .group_by(ServiceCategory.name)
    )
    tickets_by_category = {row[0]: row[1] for row in category_rows}

    # SLA metrics
    sla_breached_count = (
        await session.scalar(
            select(func.count(Ticket.id)).where(
                Ticket.organisation_id == organisation_id,
                Ticket.sla_state == SlaState.BREACHED,
            )
        )
        or 0
    )

    tickets_with_sla = (
        await session.scalar(
            select(func.count(Ticket.id)).where(
                Ticket.organisation_id == organisation_id,
                Ticket.sla_state.is_not(None),
            )
        )
        or 0
    )

    if tickets_with_sla > 0:
        compliance = round(((tickets_with_sla - sla_breached_count) / tickets_with_sla) * 100.0, 2)
    else:
        compliance = 100.0

    return AnalyticsSummaryResponse(
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        in_progress_tickets=in_progress_tickets,
        resolved_tickets=resolved_tickets,
        closed_tickets=closed_tickets,
        tickets_by_priority=tickets_by_priority,
        tickets_by_category=tickets_by_category,
        sla_breached_count=sla_breached_count,
        sla_compliance_percent=compliance,
    )


async def export_tickets_csv(
    session: AsyncSession, *, actor_id: UUID, organisation_id: UUID
) -> str:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="analytics:read",
    )

    tickets = await session.scalars(
        select(Ticket)
        .where(Ticket.organisation_id == organisation_id)
        .order_by(Ticket.created_at.desc())
        .limit(1000)
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "ticket_number",
            "title",
            "status",
            "priority",
            "created_at",
            "first_response_deadline",
            "resolution_deadline",
            "sla_state",
        ]
    )

    for t in tickets:
        writer.writerow(
            [
                str(t.id),
                t.ticket_number,
                t.title,
                t.status.value if hasattr(t.status, "value") else str(t.status),
                t.priority.value if hasattr(t.priority, "value") else str(t.priority),
                t.created_at.isoformat(),
                t.first_response_deadline.isoformat() if t.first_response_deadline else "",
                t.resolution_deadline.isoformat() if t.resolution_deadline else "",
                t.sla_state.value
                if t.sla_state and hasattr(t.sla_state, "value")
                else str(t.sla_state or ""),
            ]
        )

    return output.getvalue()
