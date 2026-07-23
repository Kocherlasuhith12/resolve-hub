from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from resolvehub.app.core.exceptions import AppError
from resolvehub.app.modules.organisations.service import require_permission
from resolvehub.app.modules.service_catalogue.models import ServiceCategory
from resolvehub.app.modules.sla.calculator import add_business_minutes
from resolvehub.app.modules.sla.models import (
    BusinessCalendar,
    CalendarHoliday,
    SlaPolicy,
    TicketSla,
)
from resolvehub.app.modules.tickets.enums import SlaState, TicketPriority, TicketStatus
from resolvehub.app.modules.tickets.models import Ticket


async def create_calendar(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    name: str,
    timezone: str,
    weekly_hours: dict[str, list[list[str]]],
) -> BusinessCalendar:
    await require_permission(
        session, user_id=actor_id, organisation_id=organisation_id, permission="sla:manage"
    )
    if await session.scalar(
        select(BusinessCalendar.id).where(
            BusinessCalendar.organisation_id == organisation_id,
            BusinessCalendar.name == name.strip(),
        )
    ):
        raise AppError("CALENDAR_EXISTS", "A business calendar with this name exists.", 409)
    calendar = BusinessCalendar(
        organisation_id=organisation_id,
        name=name.strip(),
        timezone=timezone,
        weekly_hours=weekly_hours,
        is_active=True,
    )
    session.add(calendar)
    await session.commit()
    return calendar


async def add_holiday(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    calendar_id: UUID,
    holiday_date: date,
    name: str,
) -> CalendarHoliday:
    await require_permission(
        session, user_id=actor_id, organisation_id=organisation_id, permission="sla:manage"
    )
    calendar = await session.scalar(
        select(BusinessCalendar).where(
            BusinessCalendar.id == calendar_id,
            BusinessCalendar.organisation_id == organisation_id,
        )
    )
    if calendar is None:
        raise AppError("CALENDAR_NOT_FOUND", "Business calendar was not found.", 404)
    holiday = CalendarHoliday(
        organisation_id=organisation_id,
        calendar_id=calendar.id,
        holiday_date=holiday_date,
        name=name.strip(),
    )
    session.add(holiday)
    await session.commit()
    return holiday


async def create_policy(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    category_id: UUID,
    calendar_id: UUID,
    priority: TicketPriority,
    first_response_minutes: int,
    resolution_minutes: int,
    warning_percent: int,
    pause_on_waiting: bool,
) -> SlaPolicy:
    await require_permission(
        session, user_id=actor_id, organisation_id=organisation_id, permission="sla:manage"
    )
    category = await session.scalar(
        select(ServiceCategory.id).where(
            ServiceCategory.id == category_id,
            ServiceCategory.organisation_id == organisation_id,
        )
    )
    calendar = await session.scalar(
        select(BusinessCalendar.id).where(
            BusinessCalendar.id == calendar_id,
            BusinessCalendar.organisation_id == organisation_id,
            BusinessCalendar.is_active.is_(True),
        )
    )
    if category is None or calendar is None:
        raise AppError("SLA_SCOPE_INVALID", "Category or calendar was not found.", 404)
    if resolution_minutes < first_response_minutes:
        raise AppError(
            "SLA_TARGET_INVALID", "Resolution target cannot precede first response.", 422
        )
    if await session.scalar(
        select(SlaPolicy.id).where(
            SlaPolicy.organisation_id == organisation_id,
            SlaPolicy.category_id == category_id,
            SlaPolicy.priority == priority,
        )
    ):
        raise AppError("SLA_POLICY_EXISTS", "An SLA policy already covers this scope.", 409)
    policy = SlaPolicy(
        organisation_id=organisation_id,
        category_id=category_id,
        calendar_id=calendar_id,
        priority=priority,
        first_response_minutes=first_response_minutes,
        resolution_minutes=resolution_minutes,
        warning_percent=warning_percent,
        pause_on_waiting=pause_on_waiting,
        is_active=True,
    )
    session.add(policy)
    await session.commit()
    return policy


async def list_calendars(
    session: AsyncSession, *, actor_id: UUID, organisation_id: UUID
) -> list[BusinessCalendar]:
    await require_permission(
        session, user_id=actor_id, organisation_id=organisation_id, permission="sla:manage"
    )
    return list(
        await session.scalars(
            select(BusinessCalendar)
            .where(BusinessCalendar.organisation_id == organisation_id)
            .order_by(BusinessCalendar.name)
            .limit(100)
        )
    )


async def list_policies(
    session: AsyncSession, *, actor_id: UUID, organisation_id: UUID
) -> list[SlaPolicy]:
    await require_permission(
        session, user_id=actor_id, organisation_id=organisation_id, permission="sla:manage"
    )
    return list(
        await session.scalars(
            select(SlaPolicy)
            .where(SlaPolicy.organisation_id == organisation_id)
            .order_by(SlaPolicy.created_at)
            .limit(500)
        )
    )


async def update_policy(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    policy_id: UUID,
    first_response_minutes: int | None = None,
    resolution_minutes: int | None = None,
    warning_percent: int | None = None,
    pause_on_waiting: bool | None = None,
    is_active: bool | None = None,
) -> SlaPolicy:
    await require_permission(
        session, user_id=actor_id, organisation_id=organisation_id, permission="sla:manage"
    )
    policy = await session.scalar(
        select(SlaPolicy)
        .where(
            SlaPolicy.id == policy_id,
            SlaPolicy.organisation_id == organisation_id,
        )
        .with_for_update()
    )
    if policy is None:
        raise AppError("POLICY_NOT_FOUND", "SLA policy was not found.", 404)

    new_first = (
        first_response_minutes
        if first_response_minutes is not None
        else policy.first_response_minutes
    )
    new_res = resolution_minutes if resolution_minutes is not None else policy.resolution_minutes
    if new_res < new_first:
        raise AppError(
            "SLA_TARGET_INVALID", "Resolution target cannot precede first response.", 422
        )

    if first_response_minutes is not None:
        policy.first_response_minutes = first_response_minutes
    if resolution_minutes is not None:
        policy.resolution_minutes = resolution_minutes
    if warning_percent is not None:
        policy.warning_percent = warning_percent
    if pause_on_waiting is not None:
        policy.pause_on_waiting = pause_on_waiting
    if is_active is not None:
        policy.is_active = is_active

    await session.commit()
    return policy


async def start_sla_for_ticket(
    session: AsyncSession, ticket: Ticket, now: datetime
) -> TicketSla | None:
    policy = await session.scalar(
        select(SlaPolicy).where(
            SlaPolicy.organisation_id == ticket.organisation_id,
            SlaPolicy.category_id == ticket.category_id,
            SlaPolicy.priority == ticket.priority,
            SlaPolicy.is_active.is_(True),
        )
    )
    if policy is None:
        return None
    calendar = await session.scalar(
        select(BusinessCalendar).where(
            BusinessCalendar.id == policy.calendar_id,
            BusinessCalendar.organisation_id == ticket.organisation_id,
        )
    )
    if calendar is None:
        return None
    holidays = set(
        await session.scalars(
            select(CalendarHoliday.holiday_date).where(
                CalendarHoliday.organisation_id == ticket.organisation_id,
                CalendarHoliday.calendar_id == calendar.id,
            )
        )
    )
    first_deadline = add_business_minutes(
        now,
        policy.first_response_minutes,
        timezone=calendar.timezone,
        weekly_hours=calendar.weekly_hours,
        holidays=holidays,
    )
    resolution_deadline = add_business_minutes(
        now,
        policy.resolution_minutes,
        timezone=calendar.timezone,
        weekly_hours=calendar.weekly_hours,
        holidays=holidays,
    )
    ticket.sla_state = SlaState.ACTIVE
    ticket.first_response_deadline = first_deadline
    ticket.resolution_deadline = resolution_deadline
    execution = TicketSla(
        organisation_id=ticket.organisation_id,
        ticket_id=ticket.id,
        policy_id=policy.id,
        state=SlaState.ACTIVE,
        started_at=now,
        first_response_deadline=first_deadline,
        resolution_deadline=resolution_deadline,
        accumulated_pause_seconds=0,
        workflow_id=f"sla:{ticket.organisation_id}:{ticket.id}",
        workflow_metadata={"warning_percent": policy.warning_percent},
    )
    session.add(execution)
    return execution


async def update_sla_for_transition(
    session: AsyncSession, ticket: Ticket, previous_status: TicketStatus, now: datetime
) -> None:
    execution = await session.scalar(
        select(TicketSla).where(
            TicketSla.organisation_id == ticket.organisation_id,
            TicketSla.ticket_id == ticket.id,
        )
    )
    if execution is None:
        return
    policy = await session.get(SlaPolicy, execution.policy_id)
    if ticket.status in {TicketStatus.RESOLVED, TicketStatus.CLOSED, TicketStatus.CANCELLED}:
        execution.state = SlaState.COMPLETED
        execution.completed_at = now
        ticket.sla_state = SlaState.COMPLETED
    elif policy and policy.pause_on_waiting and ticket.status == TicketStatus.WAITING_FOR_REQUESTER:
        execution.state = SlaState.PAUSED
        execution.paused_at = now
        ticket.sla_state = SlaState.PAUSED
    elif previous_status == TicketStatus.WAITING_FOR_REQUESTER and execution.paused_at:
        paused_seconds = max(0, int((now - execution.paused_at).total_seconds()))
        execution.accumulated_pause_seconds += paused_seconds
        execution.first_response_deadline += timedelta(seconds=paused_seconds)
        execution.resolution_deadline += timedelta(seconds=paused_seconds)
        execution.paused_at = None
        execution.state = SlaState.ACTIVE
        ticket.sla_state = SlaState.ACTIVE
        ticket.first_response_deadline = execution.first_response_deadline
        ticket.resolution_deadline = execution.resolution_deadline
