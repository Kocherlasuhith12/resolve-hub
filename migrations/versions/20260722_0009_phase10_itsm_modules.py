"""phase10 itsm modules

Revision ID: 20260722_0009
Revises: 20260721_0008
Create Date: 2026-07-22 12:00:00.000000
"""

from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "20260722_0009"
down_revision: str | None = "20260721_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Incidents
    op.create_table(
        "incidents",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("incident_number", sa.String(24), nullable=False, unique=True),
        sa.Column(
            "organisation_id",
            sa.UUID(),
            sa.ForeignKey("organisations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="P3 - Moderate"),
        sa.Column("service_name", sa.String(120), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="Investigating"),
        sa.Column(
            "commander_name", sa.String(120), nullable=False, server_default="DevOps On-Call"
        ),
        sa.Column("impact_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_incidents_org_created", "incidents", ["organisation_id", "created_at"])
    op.create_index("ix_incidents_incident_number", "incidents", ["incident_number"])

    # Problems
    op.create_table(
        "problems",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("problem_number", sa.String(24), nullable=False, unique=True),
        sa.Column(
            "organisation_id",
            sa.UUID(),
            sa.ForeignKey("organisations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("category", sa.String(80), nullable=False, server_default="Infrastructure"),
        sa.Column("status", sa.String(40), nullable=False, server_default="Investigation"),
        sa.Column("root_cause", sa.Text(), nullable=False, server_default=""),
        sa.Column("workaround", sa.Text(), nullable=False, server_default=""),
        sa.Column("impacted_incidents_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_problems_org_created", "problems", ["organisation_id", "created_at"])
    op.create_index("ix_problems_problem_number", "problems", ["problem_number"])

    # Changes
    op.create_table(
        "changes",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("change_number", sa.String(24), nullable=False, unique=True),
        sa.Column(
            "organisation_id",
            sa.UUID(),
            sa.ForeignKey("organisations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("change_type", sa.String(40), nullable=False, server_default="Normal"),
        sa.Column("risk_level", sa.String(40), nullable=False, server_default="Medium"),
        sa.Column("status", sa.String(40), nullable=False, server_default="CAB Approval"),
        sa.Column("owner_name", sa.String(120), nullable=False, server_default="DevOps Team"),
        sa.Column(
            "maintenance_window",
            sa.String(120),
            nullable=False,
            server_default="Sat 02:00 - 04:00 UTC",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_changes_org_created", "changes", ["organisation_id", "created_at"])
    op.create_index("ix_changes_change_number", "changes", ["change_number"])

    # Assets
    op.create_table(
        "assets",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("asset_tag", sa.String(24), nullable=False, unique=True),
        sa.Column(
            "organisation_id",
            sa.UUID(),
            sa.ForeignKey("organisations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(80), nullable=False, server_default="Laptop"),
        sa.Column("status", sa.String(40), nullable=False, server_default="In Use"),
        sa.Column("assigned_to_name", sa.String(120), nullable=False, server_default="Unassigned"),
        sa.Column("serial_number", sa.String(120), nullable=False, server_default=""),
        sa.Column("location", sa.String(120), nullable=False, server_default="Primary HQ"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_assets_org_created", "assets", ["organisation_id", "created_at"])
    op.create_index("ix_assets_asset_tag", "assets", ["asset_tag"])

    # Knowledge Articles
    op.create_table(
        "knowledge_articles",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("article_number", sa.String(24), nullable=False, unique=True),
        sa.Column(
            "organisation_id",
            sa.UUID(),
            sa.ForeignKey("organisations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("content_markdown", sa.Text(), nullable=False, server_default=""),
        sa.Column("category", sa.String(80), nullable=False, server_default="General"),
        sa.Column("author_name", sa.String(120), nullable=False, server_default="Support Team"),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("helpful_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unhelpful_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_knowledge_articles_org_created", "knowledge_articles", ["organisation_id", "created_at"]
    )
    op.create_index(
        "ix_knowledge_articles_article_number", "knowledge_articles", ["article_number"]
    )


def downgrade() -> None:
    op.drop_table("knowledge_articles")
    op.drop_table("assets")
    op.drop_table("changes")
    op.drop_table("problems")
    op.drop_table("incidents")
