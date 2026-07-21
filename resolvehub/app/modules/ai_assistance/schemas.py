from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from resolvehub.app.modules.ai_assistance.enums import (
    AiRunStatus,
    AiSuggestionKind,
    AiSuggestionStatus,
)


class AiSuggestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    ticket_id: UUID
    kind: AiSuggestionKind
    value: dict[str, object]
    confidence: float
    meets_threshold: bool
    status: AiSuggestionStatus
    decided_by_id: UUID | None
    decided_at: datetime | None
    created_at: datetime


class AiRunResponse(BaseModel):
    id: UUID
    ticket_id: UUID
    provider: str
    model_name: str
    prompt_version: str
    status: AiRunStatus
    latency_ms: int | None
    created_at: datetime
    suggestions: list[AiSuggestionResponse]


class AiSuggestionListResponse(BaseModel):
    items: list[AiSuggestionResponse]


class AiSuggestionDecision(BaseModel):
    status: AiSuggestionStatus
