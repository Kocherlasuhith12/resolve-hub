from datetime import datetime
from uuid import UUID

from sqlalchemy import Computed, DateTime, Enum, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from resolvehub.app.core.database import Base, UUIDPrimaryKeyMixin
from resolvehub.app.modules.tickets.enums import CommentKind


class TicketComment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ticket_comments"
    __table_args__ = (
        Index(
            "ix_ticket_comments_org_ticket_created", "organisation_id", "ticket_id", "created_at"
        ),
        Index("ix_ticket_comments_search_vector", "search_vector", postgresql_using="gin"),
    )

    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE")
    )
    ticket_id: Mapped[UUID] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"))
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    kind: Mapped[CommentKind] = mapped_column(Enum(CommentKind, name="comment_kind"))
    body: Mapped[str] = mapped_column(Text)
    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', coalesce(body, ''))", persisted=True),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
