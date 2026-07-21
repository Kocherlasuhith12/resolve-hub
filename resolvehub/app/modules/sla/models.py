from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from resolvehub.app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin
from resolvehub.app.modules.tickets.enums import SlaState, TicketPriority


class BusinessCalendar(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "business_calendars"
    __table_args__ = (UniqueConstraint("organisation_id", "name"),)

    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    timezone: Mapped[str] = mapped_column(String(64))
    weekly_hours: Mapped[dict[str, list[list[str]]]] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class CalendarHoliday(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "calendar_holidays"
    __table_args__ = (UniqueConstraint("organisation_id", "calendar_id", "holiday_date"),)

    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), index=True
    )
    calendar_id: Mapped[UUID] = mapped_column(
        ForeignKey("business_calendars.id", ondelete="CASCADE"), index=True
    )
    holiday_date: Mapped[date] = mapped_column(Date)
    name: Mapped[str] = mapped_column(String(120))


class SlaPolicy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sla_policies"
    __table_args__ = (
        UniqueConstraint("organisation_id", "category_id", "priority"),
        Index("ix_sla_policy_lookup", "organisation_id", "category_id", "priority", "is_active"),
        CheckConstraint("first_response_minutes > 0", name="positive_first_response"),
        CheckConstraint("resolution_minutes >= first_response_minutes", name="valid_resolution"),
        CheckConstraint("warning_percent BETWEEN 1 AND 99", name="valid_warning_percent"),
    )

    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), index=True
    )
    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("service_categories.id", ondelete="CASCADE"), index=True
    )
    calendar_id: Mapped[UUID] = mapped_column(
        ForeignKey("business_calendars.id", ondelete="RESTRICT")
    )
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority, name="ticket_priority", create_type=False)
    )
    first_response_minutes: Mapped[int] = mapped_column(Integer)
    resolution_minutes: Mapped[int] = mapped_column(Integer)
    warning_percent: Mapped[int] = mapped_column(Integer, default=80)
    pause_on_waiting: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class TicketSla(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ticket_slas"
    __table_args__ = (
        UniqueConstraint("organisation_id", "ticket_id"),
        Index("ix_ticket_slas_due", "organisation_id", "state", "resolution_deadline"),
        CheckConstraint("accumulated_pause_seconds >= 0", name="nonnegative_pause"),
    )

    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), index=True
    )
    ticket_id: Mapped[UUID] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), unique=True
    )
    policy_id: Mapped[UUID] = mapped_column(ForeignKey("sla_policies.id", ondelete="RESTRICT"))
    state: Mapped[SlaState] = mapped_column(Enum(SlaState, name="sla_state", create_type=False))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    first_response_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resolution_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accumulated_pause_seconds: Mapped[int] = mapped_column(Integer, default=0)
    warning_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    breached_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    workflow_id: Mapped[str] = mapped_column(String(200), unique=True)
    workflow_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
