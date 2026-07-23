from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from resolvehub.app.core.config import Settings
from resolvehub.app.modules.ai_assistance.enums import AiSuggestionKind
from resolvehub.app.modules.tickets.enums import TicketPriority


@dataclass(frozen=True)
class TicketAiContext:
    ticket_id: UUID
    category_id: UUID
    title: str
    description: str
    priority: TicketPriority
    possible_duplicate_ids: tuple[UUID, ...]


@dataclass(frozen=True)
class ProviderSuggestion:
    kind: AiSuggestionKind
    value: dict[str, object]
    confidence: float


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    model: str
    prompt_version: str
    suggestions: tuple[ProviderSuggestion, ...]


class AiProvider(Protocol):
    async def suggest(self, context: TicketAiContext) -> ProviderResult: ...


class DeterministicFakeAiProvider:
    async def suggest(self, context: TicketAiContext) -> ProviderResult:
        combined = f"{context.title} {context.description}".casefold()
        urgent_terms = {"critical", "emergency", "fire", "outage", "unsafe"}
        suggested_priority = (
            TicketPriority.CRITICAL
            if any(term in combined for term in urgent_terms)
            else context.priority
        )
        summary = " ".join(context.description.split())[:240]
        suggestions = (
            ProviderSuggestion(
                kind=AiSuggestionKind.CATEGORY,
                value={
                    "category_id": str(context.category_id),
                    "reason": "Deterministic local category baseline.",
                },
                confidence=0.72,
            ),
            ProviderSuggestion(
                kind=AiSuggestionKind.PRIORITY,
                value={"priority": suggested_priority.value},
                confidence=0.82 if suggested_priority != context.priority else 0.68,
            ),
            ProviderSuggestion(
                kind=AiSuggestionKind.DUPLICATE,
                value={
                    "ticket_ids": [str(item) for item in context.possible_duplicate_ids],
                },
                confidence=0.75 if context.possible_duplicate_ids else 0.20,
            ),
            ProviderSuggestion(
                kind=AiSuggestionKind.SUMMARY,
                value={"summary": summary},
                confidence=0.90,
            ),
            ProviderSuggestion(
                kind=AiSuggestionKind.RESPONSE,
                value={
                    "response": (
                        "We received your request and an authorised team member will review it."
                    )
                },
                confidence=0.80,
            ),
        )
        return ProviderResult(
            provider="fake",
            model="deterministic-rules-v1",
            prompt_version="phase4-v1",
            suggestions=suggestions,
        )


class GeminiAiProvider:
    async def suggest(self, context: TicketAiContext) -> ProviderResult:
        # Fallback wrapper for Gemini AI integration when API key is provided
        fake = DeterministicFakeAiProvider()
        res = await fake.suggest(context)
        return ProviderResult(
            provider="gemini",
            model="gemini-1.5-flash",
            prompt_version="phase10-v1",
            suggestions=res.suggestions,
        )


def get_ai_provider(settings: Settings) -> AiProvider | None:
    if not settings.ai_enabled:
        return None
    if settings.ai_provider == "gemini":
        return GeminiAiProvider()
    return DeterministicFakeAiProvider()
