import hashlib
from datetime import UTC, datetime
from decimal import Decimal
from time import perf_counter
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from resolvehub.app.core.config import Settings
from resolvehub.app.core.exceptions import AppError
from resolvehub.app.modules.ai_assistance.enums import AiRunStatus, AiSuggestionStatus
from resolvehub.app.modules.ai_assistance.models import AiAssistanceRun, AiSuggestion
from resolvehub.app.modules.ai_assistance.provider import TicketAiContext, get_ai_provider
from resolvehub.app.modules.organisations.service import require_permission
from resolvehub.app.modules.tickets.models import Ticket
from resolvehub.app.modules.tickets.service import get_accessible_ticket


def _fingerprint(ticket: Ticket) -> str:
    content = f"{ticket.title}\0{ticket.description}".encode()
    return hashlib.sha256(content).hexdigest()


async def _possible_duplicates(
    session: AsyncSession, *, organisation_id: UUID, ticket: Ticket
) -> tuple[UUID, ...]:
    tsquery = func.plainto_tsquery("english", ticket.title)
    result = await session.scalars(
        select(Ticket.id)
        .where(
            Ticket.organisation_id == organisation_id,
            Ticket.id != ticket.id,
            Ticket.search_vector.op("@@")(tsquery),
        )
        .order_by(Ticket.created_at.desc())
        .limit(5)
    )
    return tuple(result)


async def request_ai_suggestions(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    ticket_id: UUID,
    settings: Settings,
) -> tuple[AiAssistanceRun, list[AiSuggestion]]:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="ai:suggest",
    )
    ticket, _ = await get_accessible_ticket(
        session,
        actor_id=actor_id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
    )
    now = datetime.now(UTC)
    run = AiAssistanceRun(
        organisation_id=organisation_id,
        ticket_id=ticket.id,
        requested_by_id=actor_id,
        provider=settings.ai_provider,
        model_name="unavailable",
        prompt_version="unavailable",
        input_fingerprint=_fingerprint(ticket),
        status=AiRunStatus.DISABLED,
        created_at=now,
    )
    session.add(run)
    await session.flush()
    provider = get_ai_provider(settings)
    if provider is None:
        await session.commit()
        raise AppError("AI_DISABLED", "AI assistance is disabled.", 503)

    context = TicketAiContext(
        ticket_id=ticket.id,
        category_id=ticket.category_id,
        title=ticket.title,
        description=ticket.description,
        priority=ticket.priority,
        possible_duplicate_ids=await _possible_duplicates(
            session, organisation_id=organisation_id, ticket=ticket
        ),
    )
    started = perf_counter()
    try:
        result = await provider.suggest(context)
    except Exception:
        run.status = AiRunStatus.FAILED
        run.error_code = "PROVIDER_ERROR"
        run.latency_ms = round((perf_counter() - started) * 1000)
        await session.commit()
        raise AppError("AI_UNAVAILABLE", "AI assistance is temporarily unavailable.", 503) from None

    run.provider = result.provider
    run.model_name = result.model
    run.prompt_version = result.prompt_version
    run.status = AiRunStatus.SUCCEEDED
    run.latency_ms = round((perf_counter() - started) * 1000)
    suggestions = [
        AiSuggestion(
            organisation_id=organisation_id,
            ticket_id=ticket.id,
            run_id=run.id,
            kind=item.kind,
            value=item.value,
            confidence=Decimal(str(item.confidence)),
            meets_threshold=item.confidence >= settings.ai_confidence_threshold,
            status=AiSuggestionStatus.PENDING,
            created_at=now,
        )
        for item in result.suggestions
    ]
    session.add_all(suggestions)
    await session.commit()
    return run, suggestions


async def list_ai_suggestions(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    ticket_id: UUID,
) -> list[AiSuggestion]:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="ai:suggest",
    )
    await get_accessible_ticket(
        session,
        actor_id=actor_id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
    )
    return list(
        await session.scalars(
            select(AiSuggestion)
            .where(
                AiSuggestion.organisation_id == organisation_id,
                AiSuggestion.ticket_id == ticket_id,
            )
            .order_by(AiSuggestion.created_at.desc(), AiSuggestion.id.desc())
            .limit(100)
        )
    )


async def decide_ai_suggestion(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    ticket_id: UUID,
    suggestion_id: UUID,
    decision: AiSuggestionStatus,
) -> AiSuggestion:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="ai:review",
    )
    if decision not in {AiSuggestionStatus.ACCEPTED, AiSuggestionStatus.REJECTED}:
        raise AppError("AI_DECISION_INVALID", "Decision must accept or reject the suggestion.", 422)
    suggestion = await session.scalar(
        select(AiSuggestion)
        .where(
            AiSuggestion.id == suggestion_id,
            AiSuggestion.organisation_id == organisation_id,
            AiSuggestion.ticket_id == ticket_id,
        )
        .with_for_update()
    )
    if suggestion is None:
        raise AppError("AI_SUGGESTION_NOT_FOUND", "AI suggestion was not found.", 404)
    if suggestion.status != AiSuggestionStatus.PENDING:
        raise AppError("AI_SUGGESTION_ALREADY_DECIDED", "AI suggestion was already decided.", 409)
    suggestion.status = decision
    suggestion.decided_by_id = actor_id
    suggestion.decided_at = datetime.now(UTC)
    await session.commit()
    return suggestion
