"""Phase 1 identity and tenancy foundation.

Revision ID: 20260713_0001
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260713_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("verification_token_hash", sa.String(64), nullable=True),
        sa.Column("verification_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("verification_token_hash", name="uq_users_verification_token_hash"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "organisations",
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_organisations"),
    )
    op.create_index("ix_organisations_slug", "organisations", ["slug"], unique=True)
    op.create_table(
        "permissions",
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_permissions"),
        sa.UniqueConstraint("code", name="uq_permissions_code"),
    )
    op.create_table(
        "auth_sessions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("refresh_token_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by_id", sa.Uuid(), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["replaced_by_id"],
            ["auth_sessions.id"],
            name="fk_auth_sessions_replaced_by_id_auth_sessions",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_auth_sessions_user_id_users", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_auth_sessions"),
        sa.UniqueConstraint("refresh_token_hash", name="uq_auth_sessions_refresh_token_hash"),
    )
    op.create_index("ix_auth_sessions_family", "auth_sessions", ["family_id"])
    op.create_index("ix_auth_sessions_user_active", "auth_sessions", ["user_id", "revoked_at"])
    op.create_table(
        "roles",
        sa.Column("organisation_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name="fk_roles_organisation_id_organisations",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_roles"),
        sa.UniqueConstraint("organisation_id", "name", name="uq_roles_organisation_id"),
    )
    op.create_index("ix_roles_organisation_id", "roles", ["organisation_id"])
    op.create_table(
        "departments",
        sa.Column("organisation_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name="fk_departments_organisation_id_organisations",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_departments"),
        sa.UniqueConstraint("organisation_id", "name", name="uq_departments_organisation_id"),
    )
    op.create_index("ix_departments_organisation_id", "departments", ["organisation_id"])
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("permission_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
            name="fk_role_permissions_permission_id_permissions",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name="fk_role_permissions_role_id_roles", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id", name="pk_role_permissions"),
    )
    op.create_table(
        "memberships",
        sa.Column("organisation_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name="fk_memberships_organisation_id_organisations",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name="fk_memberships_role_id_roles", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_memberships_user_id_users", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_memberships"),
        sa.UniqueConstraint("organisation_id", "user_id", name="uq_memberships_organisation_id"),
    )
    op.create_index("ix_memberships_organisation_id", "memberships", ["organisation_id"])
    op.create_index("ix_memberships_user_id", "memberships", ["user_id"])
    op.create_table(
        "invitations",
        sa.Column("organisation_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("invited_by_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["invited_by_id"],
            ["users.id"],
            name="fk_invitations_invited_by_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name="fk_invitations_organisation_id_organisations",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name="fk_invitations_role_id_roles", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_invitations"),
    )
    op.create_index("ix_invitations_org_email", "invitations", ["organisation_id", "email"])
    op.create_index("ix_invitations_token_hash", "invitations", ["token_hash"], unique=True)


def downgrade() -> None:
    op.drop_table("invitations")
    op.drop_table("memberships")
    op.drop_table("role_permissions")
    op.drop_table("departments")
    op.drop_table("roles")
    op.drop_table("auth_sessions")
    op.drop_table("permissions")
    op.drop_table("organisations")
    op.drop_table("users")
