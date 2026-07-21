from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from resolvehub.app.core.database import Base, UUIDPrimaryKeyMixin
from resolvehub.app.modules.ai_assistance.enums import (
    AiRunStatus,
    AiSuggestionKind,
    AiSuggestionStatus,
)


class AiAssistanceRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ai_assistance_runs"
    __table_args__ = (
        Index(
            "ix_ai_runs_org_ticket_created",
            "organisation_id",
            "ticket_id",
            "created_at",
        ),
    )

    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE")
    )
    ticket_id: Mapped[UUID] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"))
    requested_by_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    provider: Mapped[str] = mapped_column(String(80))
    model_name: Mapped[str] = mapped_column(String(120))
    prompt_version: Mapped[str] = mapped_column(String(80))
    input_fingerprint: Mapped[str] = mapped_column(String(64))
    status: Mapped[AiRunStatus] = mapped_column(Enum(AiRunStatus, name="ai_run_status"))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AiSuggestion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ai_suggestions"
    __table_args__ = (
        Index(
            "ix_ai_suggestions_org_ticket_created",
            "organisation_id",
            "ticket_id",
            "created_at",
        ),
    )

    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE")
    )
    ticket_id: Mapped[UUID] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"))
    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("ai_assistance_runs.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[AiSuggestionKind] = mapped_column(
        Enum(AiSuggestionKind, name="ai_suggestion_kind")
    )
    value: Mapped[dict[str, Any]] = mapped_column(JSONB)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    meets_threshold: Mapped[bool] = mapped_column(Boolean)
    status: Mapped[AiSuggestionStatus] = mapped_column(
        Enum(AiSuggestionStatus, name="ai_suggestion_status")
    )
    decided_by_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
