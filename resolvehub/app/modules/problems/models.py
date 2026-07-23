from uuid import UUID

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from resolvehub.app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Problem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "problems"
    __table_args__ = (Index("ix_problems_org_created", "organisation_id", "created_at"),)

    problem_number: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(80), default="Infrastructure")
    status: Mapped[str] = mapped_column(String(40), default="Investigation")
    root_cause: Mapped[str] = mapped_column(Text, default="")
    workaround: Mapped[str] = mapped_column(Text, default="")
    impacted_incidents_count: Mapped[int] = mapped_column(Integer, default=1)
