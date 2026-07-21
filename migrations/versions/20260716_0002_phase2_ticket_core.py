"""Phase 2 catalogue and ticket core.

Revision ID: 20260716_0002
Revises: 20260713_0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260716_0002"
down_revision: str | None = "20260713_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PHASE2_PERMISSIONS = {
    "category:create": "Create service categories",
    "category:update": "Update service categories",
    "ticket:create": "Create tickets",
    "ticket:read": "Read permitted tickets",
    "ticket:read_all": "Read all organisation tickets",
    "ticket:update": "Update ticket attributes",
    "ticket:assign": "Assign tickets to agents",
    "ticket:transition": "Transition ticket state",
    "ticket:resolve": "Resolve tickets",
    "ticket:reopen": "Reopen resolved tickets",
    "ticket:escalate": "Escalate tickets",
    "comment:create": "Create public comments",
    "internal_note:create": "Create private internal notes",
    "internal_note:read": "Read private internal notes",
    "attachment:create": "Create attachment metadata",
    "audit:view": "Read audit history",
}


def upgrade() -> None:
    connection = op.get_bind()
    for code, description in PHASE2_PERMISSIONS.items():
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
            "WHERE r.name = 'Organisation Admin' AND p.code = ANY(:codes) "
            "ON CONFLICT DO NOTHING"
        ),
        {"codes": list(PHASE2_PERMISSIONS)},
    )

    ticket_priority = sa.Enum("LOW", "MEDIUM", "HIGH", "CRITICAL", name="ticket_priority")
    ticket_status = sa.Enum(
        "DRAFT",
        "SUBMITTED",
        "TRIAGED",
        "ASSIGNED",
        "IN_PROGRESS",
        "WAITING_FOR_REQUESTER",
        "RESOLVED",
        "CLOSED",
        "ESCALATED",
        "REOPENED",
        "CANCELLED",
        name="ticket_status",
    )
    ticket_source = sa.Enum(
        "WEB", "MOBILE", "EMAIL", "API", "IMPORT", "VOICE", "INTEGRATION", name="ticket_source"
    )
    sla_state = sa.Enum("NOT_STARTED", name="sla_state")
    actor_type = sa.Enum("HUMAN", "SYSTEM", "WORKFLOW", "INTEGRATION", "AI", name="actor_type")
    comment_kind = sa.Enum("PUBLIC", "INTERNAL", name="comment_kind")
    scan_status = sa.Enum("PENDING", "CLEAN", "INFECTED", "FAILED", name="malware_scan_status")

    op.create_table(
        "service_categories",
        sa.Column("organisation_id", sa.Uuid(), nullable=False),
        sa.Column("department_id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("default_priority", ticket_priority, nullable=False),
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
            ["department_id"],
            ["departments.id"],
            name="fk_service_categories_department_id_departments",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name="fk_service_categories_organisation_id_organisations",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["service_categories.id"],
            name="fk_service_categories_parent_id_service_categories",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_service_categories"),
        sa.UniqueConstraint(
            "organisation_id", "name", name="uq_service_categories_organisation_id"
        ),
    )
    op.create_index("ix_service_categories_department_id", "service_categories", ["department_id"])
    op.create_index(
        "ix_service_categories_organisation_id", "service_categories", ["organisation_id"]
    )

    op.create_table(
        "tickets",
        sa.Column("ticket_number", sa.String(24), nullable=False),
        sa.Column("organisation_id", sa.Uuid(), nullable=False),
        sa.Column("requester_id", sa.Uuid(), nullable=False),
        sa.Column("department_id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("assigned_agent_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", ticket_priority, nullable=False),
        sa.Column("status", ticket_status, nullable=False),
        sa.Column("source", ticket_source, nullable=False),
        sa.Column("sla_state", sla_state, nullable=False),
        sa.Column("first_response_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
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
        sa.CheckConstraint("version > 0", name="ck_tickets_positive_version"),
        sa.ForeignKeyConstraint(
            ["assigned_agent_id"],
            ["users.id"],
            name="fk_tickets_assigned_agent_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["service_categories.id"],
            name="fk_tickets_category_id_service_categories",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["department_id"],
            ["departments.id"],
            name="fk_tickets_department_id_departments",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name="fk_tickets_organisation_id_organisations",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["requester_id"],
            ["users.id"],
            name="fk_tickets_requester_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tickets"),
    )
    op.create_index("ix_tickets_ticket_number", "tickets", ["ticket_number"], unique=True)
    op.create_index("ix_tickets_department_id", "tickets", ["department_id"])
    op.create_index("ix_tickets_category_id", "tickets", ["category_id"])
    op.create_index("ix_tickets_org_created", "tickets", ["organisation_id", "created_at", "id"])
    op.create_index(
        "ix_tickets_org_status_priority", "tickets", ["organisation_id", "status", "priority"]
    )
    op.create_index("ix_tickets_org_assignee", "tickets", ["organisation_id", "assigned_agent_id"])

    op.create_table(
        "ticket_events",
        sa.Column("organisation_id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("actor_type", actor_type, nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("previous_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("event_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("correlation_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_id"], ["users.id"], name="fk_ticket_events_actor_id_users", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name="fk_ticket_events_organisation_id_organisations",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["tickets.id"],
            name="fk_ticket_events_ticket_id_tickets",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ticket_events"),
    )
    op.create_index("ix_ticket_events_created_at", "ticket_events", ["created_at"])
    op.create_index(
        "ix_ticket_events_org_ticket_created",
        "ticket_events",
        ["organisation_id", "ticket_id", "created_at"],
    )

    op.create_table(
        "idempotency_records",
        sa.Column("organisation_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("operation", sa.String(80), nullable=False),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("response_body", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name="fk_idempotency_records_actor_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name="fk_idempotency_records_organisation_id_organisations",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_idempotency_records"),
    )
    op.create_index("ix_idempotency_records_expires_at", "idempotency_records", ["expires_at"])
    op.create_index(
        "uq_idempotency_scope",
        "idempotency_records",
        ["organisation_id", "actor_id", "operation", "key"],
        unique=True,
    )

    op.create_table(
        "ticket_comments",
        sa.Column("organisation_id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("kind", comment_kind, nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["users.id"],
            name="fk_ticket_comments_author_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name="fk_ticket_comments_organisation_id_organisations",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["tickets.id"],
            name="fk_ticket_comments_ticket_id_tickets",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ticket_comments"),
    )
    op.create_index("ix_ticket_comments_created_at", "ticket_comments", ["created_at"])
    op.create_index(
        "ix_ticket_comments_org_ticket_created",
        "ticket_comments",
        ["organisation_id", "ticket_id", "created_at"],
    )

    op.create_table(
        "attachments",
        sa.Column("organisation_id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("uploaded_by_id", sa.Uuid(), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(120), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("upload_completed", sa.Boolean(), nullable=False),
        sa.Column("scan_status", scan_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint(
            "size_bytes > 0 AND size_bytes <= 10485760", name="ck_attachments_valid_size"
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name="fk_attachments_organisation_id_organisations",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["tickets.id"],
            name="fk_attachments_ticket_id_tickets",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by_id"],
            ["users.id"],
            name="fk_attachments_uploaded_by_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_attachments"),
    )
    op.create_index("ix_attachments_created_at", "attachments", ["created_at"])
    op.create_index("ix_attachments_org_ticket", "attachments", ["organisation_id", "ticket_id"])
    op.create_index("ix_attachments_storage_key", "attachments", ["storage_key"], unique=True)


def downgrade() -> None:
    op.drop_table("attachments")
    op.drop_table("ticket_comments")
    op.drop_table("idempotency_records")
    op.drop_table("ticket_events")
    op.drop_table("tickets")
    op.drop_table("service_categories")
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "DELETE FROM role_permissions WHERE permission_id IN (SELECT id FROM permissions WHERE code = ANY(:codes))"
        ),
        {"codes": list(PHASE2_PERMISSIONS)},
    )
    connection.execute(
        sa.text("DELETE FROM permissions WHERE code = ANY(:codes)"),
        {"codes": list(PHASE2_PERMISSIONS)},
    )
    for enum_name in (
        "malware_scan_status",
        "comment_kind",
        "actor_type",
        "sla_state",
        "ticket_source",
        "ticket_status",
        "ticket_priority",
    ):
        sa.Enum(name=enum_name).drop(connection, checkfirst=True)
