from uuid import UUID

from fastapi import APIRouter

from resolvehub.app.core.dependencies import AppSettings, CurrentPrincipal, DbSession
from resolvehub.app.modules.ai_assistance.schemas import (
    AiRunResponse,
    AiSuggestionDecision,
    AiSuggestionListResponse,
    AiSuggestionResponse,
)
from resolvehub.app.modules.ai_assistance.service import (
    decide_ai_suggestion,
    list_ai_suggestions,
    request_ai_suggestions,
)

router = APIRouter(
    prefix="/organisations/{organisation_id}/tickets/{ticket_id}/ai",
    tags=["AI Assistance"],
)


@router.post(
    "/suggestions",
    response_model=AiRunResponse,
    summary="Request optional AI suggestions",
    description=(
        "Creates audited suggestions without changing the ticket. Returns 503 when AI is disabled "
        "or unavailable; ticket operations remain independent."
    ),
)
async def suggestions_request(
    organisation_id: UUID,
    ticket_id: UUID,
    principal: CurrentPrincipal,
    session: DbSession,
    settings: AppSettings,
) -> AiRunResponse:
    run, suggestions = await request_ai_suggestions(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
        settings=settings,
    )
    return AiRunResponse(
        id=run.id,
        ticket_id=run.ticket_id,
        provider=run.provider,
        model_name=run.model_name,
        prompt_version=run.prompt_version,
        status=run.status,
        latency_ms=run.latency_ms,
        created_at=run.created_at,
        suggestions=[AiSuggestionResponse.model_validate(item) for item in suggestions],
    )


@router.get("/suggestions", response_model=AiSuggestionListResponse)
async def suggestions_list(
    organisation_id: UUID,
    ticket_id: UUID,
    principal: CurrentPrincipal,
    session: DbSession,
) -> AiSuggestionListResponse:
    items = await list_ai_suggestions(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
    )
    return AiSuggestionListResponse(
        items=[AiSuggestionResponse.model_validate(item) for item in items]
    )


@router.post(
    "/suggestions/{suggestion_id}/decision",
    response_model=AiSuggestionResponse,
)
async def suggestions_decide(
    organisation_id: UUID,
    ticket_id: UUID,
    suggestion_id: UUID,
    payload: AiSuggestionDecision,
    principal: CurrentPrincipal,
    session: DbSession,
) -> AiSuggestionResponse:
    suggestion = await decide_ai_suggestion(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
        suggestion_id=suggestion_id,
        decision=payload.status,
    )
    return AiSuggestionResponse.model_validate(suggestion)
