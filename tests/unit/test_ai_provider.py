from uuid import uuid4

import pytest

from resolvehub.app.core.config import Settings
from resolvehub.app.modules.ai_assistance.enums import AiSuggestionKind
from resolvehub.app.modules.ai_assistance.provider import (
    DeterministicFakeAiProvider,
    TicketAiContext,
    get_ai_provider,
)
from resolvehub.app.modules.tickets.enums import TicketPriority


def test_ai_provider_is_disabled_by_default() -> None:
    assert get_ai_provider(Settings()) is None


@pytest.mark.asyncio
async def test_fake_ai_provider_is_deterministic_and_advisory() -> None:
    duplicate_id = uuid4()
    context = TicketAiContext(
        ticket_id=uuid4(),
        category_id=uuid4(),
        title="Critical network outage",
        description="The main router is offline for the north building.",
        priority=TicketPriority.MEDIUM,
        possible_duplicate_ids=(duplicate_id,),
    )
    provider = DeterministicFakeAiProvider()

    first = await provider.suggest(context)
    second = await provider.suggest(context)

    assert first == second
    assert first.provider == "fake"
    by_kind = {item.kind: item for item in first.suggestions}
    assert by_kind[AiSuggestionKind.PRIORITY].value == {"priority": "CRITICAL"}
    assert by_kind[AiSuggestionKind.DUPLICATE].value == {"ticket_ids": [str(duplicate_id)]}
    assert by_kind[AiSuggestionKind.SUMMARY].value["summary"]


def test_enabled_settings_select_fake_provider() -> None:
    settings = Settings(ai_enabled=True)
    assert isinstance(get_ai_provider(settings), DeterministicFakeAiProvider)
