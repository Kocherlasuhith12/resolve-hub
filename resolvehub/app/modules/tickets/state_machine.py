from dataclasses import dataclass

from resolvehub.app.core.exceptions import AppError
from resolvehub.app.modules.tickets.enums import TicketStatus

ALLOWED_TRANSITIONS: dict[TicketStatus, frozenset[TicketStatus]] = {
    TicketStatus.DRAFT: frozenset({TicketStatus.SUBMITTED, TicketStatus.CANCELLED}),
    TicketStatus.SUBMITTED: frozenset({TicketStatus.TRIAGED, TicketStatus.CANCELLED}),
    TicketStatus.TRIAGED: frozenset(
        {TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS, TicketStatus.CANCELLED}
    ),
    TicketStatus.ASSIGNED: frozenset({TicketStatus.IN_PROGRESS, TicketStatus.CANCELLED}),
    TicketStatus.IN_PROGRESS: frozenset(
        {
            TicketStatus.WAITING_FOR_REQUESTER,
            TicketStatus.RESOLVED,
            TicketStatus.ESCALATED,
            TicketStatus.CANCELLED,
        }
    ),
    TicketStatus.WAITING_FOR_REQUESTER: frozenset(
        {TicketStatus.IN_PROGRESS, TicketStatus.CANCELLED}
    ),
    TicketStatus.ESCALATED: frozenset({TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED}),
    TicketStatus.RESOLVED: frozenset({TicketStatus.CLOSED, TicketStatus.REOPENED}),
    TicketStatus.REOPENED: frozenset({TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS}),
    TicketStatus.CLOSED: frozenset(),
    TicketStatus.CANCELLED: frozenset(),
}

REASON_REQUIRED = frozenset({TicketStatus.CANCELLED, TicketStatus.ESCALATED, TicketStatus.REOPENED})


@dataclass(frozen=True)
class TransitionDecision:
    previous: TicketStatus
    current: TicketStatus


def validate_transition(
    *,
    current: TicketStatus,
    requested: TicketStatus,
    reason: str | None,
    assigned: bool,
) -> TransitionDecision:
    if requested not in ALLOWED_TRANSITIONS[current]:
        raise AppError(
            "TICKET_TRANSITION_NOT_ALLOWED",
            "The requested ticket transition is not allowed.",
            409,
            {"current_status": current, "requested_status": requested},
        )
    if requested in REASON_REQUIRED and not reason:
        raise AppError(
            "TICKET_TRANSITION_REASON_REQUIRED",
            "A reason is required for this transition.",
            422,
        )
    if requested in {TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS} and not assigned:
        raise AppError(
            "TICKET_ASSIGNMENT_REQUIRED",
            "An assigned agent is required for this transition.",
            409,
        )
    return TransitionDecision(previous=current, current=requested)
