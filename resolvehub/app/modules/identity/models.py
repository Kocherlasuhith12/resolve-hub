from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, Computed, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from resolvehub.app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        Index(
            "ix_users_display_name_search_vector",
            "display_name_search_vector",
            postgresql_using="gin",
        ),
    )

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    display_name: Mapped[str] = mapped_column(String(120))
    display_name_search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', coalesce(display_name, ''))", persisted=True),
    )
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    verification_token_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    verification_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    sessions: Mapped[list["AuthSession"]] = relationship(back_populates="user")


class AuthSession(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "auth_sessions"
    __table_args__ = (
        Index("ix_auth_sessions_user_active", "user_id", "revoked_at"),
        Index("ix_auth_sessions_family", "family_id"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    family_id: Mapped[UUID]
    refresh_token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    csrf_token_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by_id: Mapped[UUID | None] = mapped_column(ForeignKey("auth_sessions.id"))
    user_agent: Mapped[str | None] = mapped_column(String(512))
    ip_address: Mapped[str | None] = mapped_column(String(64))

    user: Mapped[User] = relationship(back_populates="sessions")
