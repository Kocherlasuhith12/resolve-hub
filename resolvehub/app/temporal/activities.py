from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from temporalio import activity

from resolvehub.app.core.database import async_session_factory
from resolvehub.app.modules.notifications.outbox import enqueue_event
from resolvehub.app.modules.sla.models import TicketSla
from resolvehub.app.modules.tickets.enums import SlaState
from resolvehub.app.modules.tickets.models import Ticket, TicketEvent


@activity.defn(name="record_sla_event")
async def record_sla_event(organisation_id: str, ticket_id: str, event_type: str) -> None:
    async with async_session_factory() as session:
        await record_sla_event_in_session(
            session,
            organisation_id=UUID(organisation_id),
            ticket_id=UUID(ticket_id),
            event_type=event_type,
        )


async def record_sla_event_in_session(
    session: AsyncSession, *, organisation_id: UUID, ticket_id: UUID, event_type: str
) -> None:
    ticket = await session.scalar(
        select(Ticket)
        .where(Ticket.organisation_id == organisation_id, Ticket.id == ticket_id)
        .with_for_update()
    )
    execution = await session.scalar(
        select(TicketSla).where(
            TicketSla.organisation_id == organisation_id, TicketSla.ticket_id == ticket_id
        )
    )
    if ticket is None or execution is None or execution.state == SlaState.COMPLETED:
        return
    dedupe_key = f"sla:{ticket_id}:{event_type}"
    if await session.scalar(
        select(TicketEvent.id).where(
            TicketEvent.organisation_id == organisation_id,
            TicketEvent.ticket_id == ticket_id,
            TicketEvent.event_type == event_type,
        )
    ):
        return
    now = datetime.now(UTC)
    session.add(
        TicketEvent(
            organisation_id=organisation_id,
            ticket_id=ticket_id,
            actor_id=None,
            actor_type="WORKFLOW",
            event_type=event_type,
            previous_values=None,
            new_values={"sla_state": event_type.removeprefix("SLA_")},
            event_metadata={},
            correlation_id=uuid4(),
            created_at=now,
        )
    )
    if event_type == "SLA_WARNING":
        execution.state = SlaState.WARNING
        execution.warning_at = now
        ticket.sla_state = SlaState.WARNING
    else:
        execution.state = SlaState.BREACHED
        execution.breached_at = now
        ticket.sla_state = SlaState.BREACHED
    recipients = {ticket.requester_id}
    if ticket.assigned_agent_id:
        recipients.add(ticket.assigned_agent_id)
    enqueue_event(
        session,
        organisation_id=organisation_id,
        aggregate_type="ticket",
        aggregate_id=ticket_id,
        event_type=event_type,
        payload={
            "ticket_number": ticket.ticket_number,
            "recipient_ids": [str(item) for item in sorted(recipients, key=str)],
            "visibility": "public",
        },
        dedupe_key=dedupe_key,
    )
    await session.commit()
