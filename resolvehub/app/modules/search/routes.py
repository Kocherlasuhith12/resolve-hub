from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from resolvehub.app.core.dependencies import CurrentPrincipal, DbSession
from resolvehub.app.modules.search.schemas import TicketSearchResponse
from resolvehub.app.modules.search.service import search_tickets
from resolvehub.app.modules.tickets.enums import SlaState, TicketPriority, TicketStatus
from resolvehub.app.modules.tickets.schemas import TicketResponse

router = APIRouter(prefix="/organisations/{organisation_id}/search", tags=["Search"])


@router.get(
    "/tickets",
    response_model=TicketSearchResponse,
    summary="Search accessible tickets",
    description=(
        "Uses tenant-isolated PostgreSQL full-text search across tickets, categories, requester "
        "display names, and comments visible to the current membership."
    ),
)
async def tickets_search(
    organisation_id: UUID,
    principal: CurrentPrincipal,
    session: DbSession,
    query: Annotated[str, Query(min_length=2, max_length=200)],
    ticket_status: Annotated[TicketStatus | None, Query(alias="status")] = None,
    priority: TicketPriority | None = None,
    department_id: UUID | None = None,
    assignee_id: UUID | None = None,
    category_id: UUID | None = None,
    requester_id: UUID | None = None,
    sla_state: SlaState | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    updated_from: datetime | None = None,
    updated_to: datetime | None = None,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> TicketSearchResponse:
    items, next_cursor = await search_tickets(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        query=query,
        status=ticket_status,
        priority=priority,
        department_id=department_id,
        assignee_id=assignee_id,
        category_id=category_id,
        requester_id=requester_id,
        sla_state=sla_state,
        created_from=created_from,
        created_to=created_to,
        updated_from=updated_from,
        updated_to=updated_to,
        cursor=cursor,
        limit=limit,
    )
    return TicketSearchResponse(
        items=[TicketResponse.model_validate(item) for item in items],
        next_cursor=next_cursor,
    )
