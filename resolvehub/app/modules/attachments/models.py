from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from resolvehub.app.core.database import Base, UUIDPrimaryKeyMixin
from resolvehub.app.modules.tickets.enums import MalwareScanStatus


class Attachment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "attachments"
    __table_args__ = (
        CheckConstraint("size_bytes > 0 AND size_bytes <= 10485760", name="valid_size"),
        Index("ix_attachments_org_ticket", "organisation_id", "ticket_id"),
        Index("ix_attachments_storage_key", "storage_key", unique=True),
    )

    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE")
    )
    ticket_id: Mapped[UUID] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"))
    uploaded_by_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    upload_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    scan_status: Mapped[MalwareScanStatus] = mapped_column(
        Enum(MalwareScanStatus, name="malware_scan_status")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
