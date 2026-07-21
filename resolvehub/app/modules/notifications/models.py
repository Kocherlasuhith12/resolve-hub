from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from resolvehub.app.core.database import Base, UUIDPrimaryKeyMixin


class OutboxStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


class DeliveryStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class OutboxRecord(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "outbox_records"
    __table_args__ = (
        UniqueConstraint("organisation_id", "dedupe_key"),
        Index("ix_outbox_claim", "status", "available_at", "created_at"),
    )

    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), index=True
    )
    aggregate_type: Mapped[str] = mapped_column(String(80))
    aggregate_id: Mapped[UUID]
    event_type: Mapped[str] = mapped_column(String(80))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    dedupe_key: Mapped[str] = mapped_column(String(200))
    status: Mapped[OutboxStatus] = mapped_column(Enum(OutboxStatus, name="outbox_status"))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Notification(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("organisation_id", "user_id", "source_outbox_id"),
        Index("ix_notifications_user_created", "organisation_id", "user_id", "created_at"),
    )

    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE")
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    source_outbox_id: Mapped[UUID] = mapped_column(
        ForeignKey("outbox_records.id", ondelete="CASCADE")
    )
    kind: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    resource_type: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[UUID]
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DeliveryAttempt(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "delivery_attempts"
    __table_args__ = (UniqueConstraint("outbox_id", "channel", "recipient", "attempt_number"),)

    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), index=True
    )
    outbox_id: Mapped[UUID] = mapped_column(ForeignKey("outbox_records.id", ondelete="CASCADE"))
    channel: Mapped[str] = mapped_column(String(40))
    recipient: Mapped[str] = mapped_column(String(320))
    attempt_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[DeliveryStatus] = mapped_column(Enum(DeliveryStatus, name="delivery_status"))
    provider_reference: Mapped[str | None] = mapped_column(String(200))
    error_code: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
