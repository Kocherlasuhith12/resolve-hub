from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Computed,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from resolvehub.app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin
from resolvehub.app.modules.tickets.enums import (
    ActorType,
    SlaState,
    TicketPriority,
    TicketSource,
    TicketStatus,
)


class Ticket(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tickets"
    __table_args__ = (
        CheckConstraint("version > 0", name="positive_version"),
        Index("ix_tickets_org_created", "organisation_id", "created_at", "id"),
        Index("ix_tickets_org_status_priority", "organisation_id", "status", "priority"),
        Index("ix_tickets_org_assignee", "organisation_id", "assigned_agent_id"),
        Index("ix_tickets_search_vector", "search_vector", postgresql_using="gin"),
    )

    ticket_number: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE")
    )
    requester_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    department_id: Mapped[UUID] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), index=True
    )
    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("service_categories.id", ondelete="RESTRICT"), index=True
    )
    assigned_agent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed(
            "setweight(to_tsvector('english', coalesce(ticket_number, '')), 'A') || "
            "setweight(to_tsvector('english', coalesce(title, '')), 'A') || "
            "setweight(to_tsvector('english', coalesce(description, '')), 'B')",
            persisted=True,
        ),
    )
    priority: Mapped[TicketPriority] = mapped_column(Enum(TicketPriority, name="ticket_priority"))
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus, name="ticket_status"))
    source: Mapped[TicketSource] = mapped_column(Enum(TicketSource, name="ticket_source"))
    sla_state: Mapped[SlaState] = mapped_column(Enum(SlaState, name="sla_state"))
    first_response_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)


class TicketEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ticket_events"
    __table_args__ = (
        Index("ix_ticket_events_org_ticket_created", "organisation_id", "ticket_id", "created_at"),
    )

    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE")
    )
    ticket_id: Mapped[UUID] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"))
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    actor_type: Mapped[ActorType] = mapped_column(Enum(ActorType, name="actor_type"))
    event_type: Mapped[str] = mapped_column(String(80))
    previous_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    new_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    event_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    correlation_id: Mapped[UUID]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class IdempotencyRecord(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        Index(
            "uq_idempotency_scope",
            "organisation_id",
            "actor_id",
            "operation",
            "key",
            unique=True,
        ),
    )

    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE")
    )
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    operation: Mapped[str] = mapped_column(String(80))
    key: Mapped[str] = mapped_column(String(128))
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    response_status: Mapped[int]
    response_body: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
