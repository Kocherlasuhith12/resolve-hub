from uuid import UUID

from sqlalchemy import Boolean, Computed, Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from resolvehub.app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin
from resolvehub.app.modules.tickets.enums import TicketPriority


class ServiceCategory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "service_categories"
    __table_args__ = (
        UniqueConstraint("organisation_id", "name"),
        Index("ix_service_categories_search_vector", "search_vector", postgresql_using="gin"),
    )

    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), index=True
    )
    department_id: Mapped[UUID] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), index=True
    )
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("service_categories.id", ondelete="RESTRICT")
    )
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(String(500))
    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed(
            "setweight(to_tsvector('english', coalesce(name, '')), 'A') || "
            "setweight(to_tsvector('english', coalesce(description, '')), 'B')",
            persisted=True,
        ),
    )
    default_priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority, name="ticket_priority")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
