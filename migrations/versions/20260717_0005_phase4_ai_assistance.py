"""phase4 ai assistance

Revision ID: 20260717_0005
Revises: 20260717_0004
Create Date: 2026-07-17 11:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260717_0005"
down_revision: str | None = "20260717_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    connection = op.get_bind()
    permissions = {
        "ai:suggest": "Request optional AI suggestions for accessible tickets",
        "ai:review": "Accept or reject AI suggestions",
    }
    for code, description in permissions.items():
        connection.execute(
            sa.text(
                "INSERT INTO permissions (id, code, description) "
                "VALUES (gen_random_uuid(), :code, :description) ON CONFLICT (code) DO NOTHING"
            ),
            {"code": code, "description": description},
        )
    connection.execute(
        sa.text(
            "INSERT INTO role_permissions (role_id, permission_id) "
            "SELECT r.id, p.id FROM roles r CROSS JOIN permissions p "
            "WHERE r.name IN ('Organisation Admin', 'Agent') AND p.code = ANY(:codes) "
            "ON CONFLICT DO NOTHING"
        ),
        {"codes": list(permissions)},
    )

    op.create_table(
        "ai_assistance_runs",
        sa.Column("organisation_id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("requested_by_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model_name", sa.String(length=120), nullable=False),
        sa.Column("prompt_version", sa.String(length=80), nullable=False),
        sa.Column("input_fingerprint", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.Enum("SUCCEEDED", "FAILED", "DISABLED", name="ai_run_status"),
            nullable=False,
        ),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_runs_org_ticket_created",
        "ai_assistance_runs",
        ["organisation_id", "ticket_id", "created_at"],
    )
    op.create_table(
        "ai_suggestions",
        sa.Column("organisation_id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "CATEGORY",
                "PRIORITY",
                "DUPLICATE",
                "SUMMARY",
                "RESPONSE",
                name="ai_suggestion_kind",
            ),
            nullable=False,
        ),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("meets_threshold", sa.Boolean(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "ACCEPTED", "REJECTED", name="ai_suggestion_status"),
            nullable=False,
        ),
        sa.Column("decided_by_id", sa.Uuid(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["ai_assistance_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["decided_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_suggestions_run_id", "ai_suggestions", ["run_id"])
    op.create_index(
        "ix_ai_suggestions_org_ticket_created",
        "ai_suggestions",
        ["organisation_id", "ticket_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("ai_suggestions")
    op.drop_table("ai_assistance_runs")
    bind = op.get_bind()
    postgresql.ENUM(name="ai_suggestion_status").drop(bind, checkfirst=True)
    postgresql.ENUM(name="ai_suggestion_kind").drop(bind, checkfirst=True)
    postgresql.ENUM(name="ai_run_status").drop(bind, checkfirst=True)
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "DELETE FROM role_permissions WHERE permission_id IN "
            "(SELECT id FROM permissions WHERE code IN ('ai:suggest', 'ai:review'))"
        )
    )
    connection.execute(sa.text("DELETE FROM permissions WHERE code IN ('ai:suggest', 'ai:review')"))
