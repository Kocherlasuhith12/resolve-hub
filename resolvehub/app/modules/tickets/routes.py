from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, Query, Request, Response, status

from resolvehub.app.core.dependencies import CurrentPrincipal, DbSession
from resolvehub.app.modules.tickets.enums import TicketPriority, TicketStatus
from resolvehub.app.modules.tickets.schemas import (
    AssignmentCandidateResponse,
    AttachmentCreate,
    AttachmentResponse,
    CommentCreate,
    CommentListResponse,
    CommentResponse,
    TicketAssignment,
    TicketCreate,
    TicketEventListResponse,
    TicketEventResponse,
    TicketListResponse,
    TicketResponse,
    TicketTransition,
)
from resolvehub.app.modules.tickets.service import (
    add_comment,
    assign_ticket,
    create_attachment_metadata,
    create_ticket,
    get_accessible_ticket,
    list_assignment_candidates,
    list_comments,
    list_events,
    list_tickets,
    transition_ticket,
)

router = APIRouter(prefix="/organisations/{organisation_id}/tickets", tags=["Tickets"])


def correlation_id(request: Request) -> UUID:
    return UUID(request.state.request_id)


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def tickets_create(
    organisation_id: UUID,
    payload: TicketCreate,
    request: Request,
    response: Response,
    principal: CurrentPrincipal,
    session: DbSession,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> TicketResponse:
    key = idempotency_key or str(uuid4())
    ticket, replayed = await create_ticket(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        category_id=payload.category_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        source=payload.source,
        idempotency_key=key,
        correlation_id=correlation_id(request),
    )
    if replayed:
        response.status_code = status.HTTP_200_OK
    return TicketResponse.model_validate(ticket)


@router.get("", response_model=TicketListResponse)
async def tickets_list(
    organisation_id: UUID,
    principal: CurrentPrincipal,
    session: DbSession,
    ticket_status: Annotated[TicketStatus | None, Query(alias="status")] = None,
    priority: TicketPriority | None = None,
    department_id: UUID | None = None,
    assignee_id: UUID | None = None,
    category_id: UUID | None = None,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> TicketListResponse:
    items, next_cursor = await list_tickets(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        status=ticket_status,
        priority=priority,
        department_id=department_id,
        assignee_id=assignee_id,
        category_id=category_id,
        cursor=cursor,
        limit=limit,
    )
    return TicketListResponse(
        items=[TicketResponse.model_validate(item) for item in items], next_cursor=next_cursor
    )


@router.get("/assignment-candidates", response_model=list[AssignmentCandidateResponse])
async def assignment_candidates_list(
    organisation_id: UUID,
    principal: CurrentPrincipal,
    session: DbSession,
) -> list[AssignmentCandidateResponse]:
    items = await list_assignment_candidates(
        session, actor_id=principal.user.id, organisation_id=organisation_id
    )
    return [
        AssignmentCandidateResponse(user_id=item.id, display_name=item.display_name)
        for item in items
    ]


@router.get("/{ticket_id}", response_model=TicketResponse)
async def tickets_detail(
    organisation_id: UUID,
    ticket_id: UUID,
    principal: CurrentPrincipal,
    session: DbSession,
) -> TicketResponse:
    ticket, _ = await get_accessible_ticket(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
    )
    return TicketResponse.model_validate(ticket)


@router.post("/{ticket_id}/assignment", response_model=TicketResponse)
async def tickets_assign(
    organisation_id: UUID,
    ticket_id: UUID,
    payload: TicketAssignment,
    request: Request,
    principal: CurrentPrincipal,
    session: DbSession,
) -> TicketResponse:
    ticket = await assign_ticket(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
        assigned_agent_id=payload.assigned_agent_id,
        expected_version=payload.version,
        correlation_id=correlation_id(request),
    )
    return TicketResponse.model_validate(ticket)


@router.post("/{ticket_id}/transitions", response_model=TicketResponse)
async def tickets_transition(
    organisation_id: UUID,
    ticket_id: UUID,
    payload: TicketTransition,
    request: Request,
    principal: CurrentPrincipal,
    session: DbSession,
) -> TicketResponse:
    ticket = await transition_ticket(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
        requested_status=payload.status,
        expected_version=payload.version,
        reason=payload.reason,
        correlation_id=correlation_id(request),
    )
    return TicketResponse.model_validate(ticket)


@router.post(
    "/{ticket_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED
)
async def comments_create(
    organisation_id: UUID,
    ticket_id: UUID,
    payload: CommentCreate,
    request: Request,
    principal: CurrentPrincipal,
    session: DbSession,
) -> CommentResponse:
    comment = await add_comment(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
        kind=payload.kind,
        body=payload.body,
        correlation_id=correlation_id(request),
    )
    return CommentResponse.model_validate(comment)


@router.get("/{ticket_id}/comments", response_model=CommentListResponse)
async def comments_list(
    organisation_id: UUID,
    ticket_id: UUID,
    principal: CurrentPrincipal,
    session: DbSession,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> CommentListResponse:
    items, next_cursor = await list_comments(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
        cursor=cursor,
        limit=limit,
    )
    return CommentListResponse(
        items=[CommentResponse.model_validate(item) for item in items], next_cursor=next_cursor
    )


@router.get("/{ticket_id}/timeline", response_model=TicketEventListResponse)
async def timeline_list(
    organisation_id: UUID,
    ticket_id: UUID,
    principal: CurrentPrincipal,
    session: DbSession,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> TicketEventListResponse:
    items, next_cursor = await list_events(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
        cursor=cursor,
        limit=limit,
    )
    return TicketEventListResponse(
        items=[TicketEventResponse.model_validate(item) for item in items],
        next_cursor=next_cursor,
    )


@router.post(
    "/{ticket_id}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def attachments_create(
    organisation_id: UUID,
    ticket_id: UUID,
    payload: AttachmentCreate,
    request: Request,
    principal: CurrentPrincipal,
    session: DbSession,
) -> AttachmentResponse:
    attachment = await create_attachment_metadata(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
        filename=payload.filename,
        content_type=payload.content_type,
        size_bytes=payload.size_bytes,
        correlation_id=correlation_id(request),
    )
    return AttachmentResponse.model_validate(attachment)
