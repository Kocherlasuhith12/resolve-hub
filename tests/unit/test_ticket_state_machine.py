import pytest

from resolvehub.app.core.exceptions import AppError
from resolvehub.app.modules.tickets.enums import TicketStatus
from resolvehub.app.modules.tickets.state_machine import validate_transition


def test_valid_transition_returns_decision() -> None:
    decision = validate_transition(
        current=TicketStatus.SUBMITTED,
        requested=TicketStatus.TRIAGED,
        reason=None,
        assigned=False,
    )
    assert decision.previous == TicketStatus.SUBMITTED
    assert decision.current == TicketStatus.TRIAGED


def test_rejects_transition_not_in_state_graph() -> None:
    with pytest.raises(AppError, match="not allowed") as error:
        validate_transition(
            current=TicketStatus.SUBMITTED,
            requested=TicketStatus.RESOLVED,
            reason=None,
            assigned=False,
        )
    assert error.value.code == "TICKET_TRANSITION_NOT_ALLOWED"


def test_requires_assignment_for_in_progress() -> None:
    with pytest.raises(AppError) as error:
        validate_transition(
            current=TicketStatus.TRIAGED,
            requested=TicketStatus.IN_PROGRESS,
            reason=None,
            assigned=False,
        )
    assert error.value.code == "TICKET_ASSIGNMENT_REQUIRED"


def test_requires_reason_for_escalation() -> None:
    with pytest.raises(AppError) as error:
        validate_transition(
            current=TicketStatus.IN_PROGRESS,
            requested=TicketStatus.ESCALATED,
            reason=None,
            assigned=True,
        )
    assert error.value.code == "TICKET_TRANSITION_REASON_REQUIRED"
