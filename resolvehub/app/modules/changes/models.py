from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from resolvehub.app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ChangeRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "changes"
    __table_args__ = (Index("ix_changes_org_created", "organisation_id", "created_at"),)

    change_number: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    change_type: Mapped[str] = mapped_column(String(40), default="Normal")
    risk_level: Mapped[str] = mapped_column(String(40), default="Medium")
    status: Mapped[str] = mapped_column(String(40), default="CAB Approval")
    owner_name: Mapped[str] = mapped_column(String(120), default="DevOps Team")
    maintenance_window: Mapped[str] = mapped_column(String(120), default="Sat 02:00 - 04:00 UTC")
