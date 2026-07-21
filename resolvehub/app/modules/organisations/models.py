from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from resolvehub.app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Organisation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "organisations"

    name: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Permission(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(String(255))


class Role(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("organisation_id", "name"),)

    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(80))
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    permissions: Mapped[list[Permission]] = relationship(
        secondary=role_permissions, lazy="selectin"
    )


class Membership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("organisation_id", "user_id"),)

    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[Role] = relationship(lazy="joined")


class Invitation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "invitations"
    __table_args__ = (
        Index("ix_invitations_org_email", "organisation_id", "email"),
        Index("ix_invitations_token_hash", "token_hash", unique=True),
    )

    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE")
    )
    email: Mapped[str] = mapped_column(String(320))
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"))
    invited_by_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    token_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Department(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "departments"
    __table_args__ = (UniqueConstraint("organisation_id", "name"),)

    organisation_id: Mapped[UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
