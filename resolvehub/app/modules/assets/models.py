from uuid import UUID

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from resolvehub.app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AssetItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assets"
    __table_args__ = (Index("ix_assets_org_created", "organisation_id", "created_at"),)

    asset_tag: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(80), default="Laptop")
    status: Mapped[str] = mapped_column(String(40), default="In Use")
    assigned_to_name: Mapped[str] = mapped_column(String(120), default="Unassigned")
    serial_number: Mapped[str] = mapped_column(String(120), default="")
    location: Mapped[str] = mapped_column(String(120), default="Primary HQ")
