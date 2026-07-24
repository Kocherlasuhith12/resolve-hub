"""stripe billing tables

Revision ID: 20260723_0010
Revises: 20260722_0009
Create Date: 2026-07-23 06:00:00.000000
"""

from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "20260723_0010"
down_revision: str | None = "20260722_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Subscriptions
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column(
            "organisation_id",
            sa.UUID(),
            sa.ForeignKey("organisations.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("stripe_customer_id", sa.String(255), nullable=False, server_default=""),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=False, server_default=""),
        sa.Column("stripe_price_id", sa.String(255), nullable=False, server_default=""),
        sa.Column("plan_name", sa.String(100), nullable=False, server_default="Starter Plan"),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_subscriptions_org_created", "subscriptions", ["organisation_id", "created_at"]
    )
    op.create_index("ix_subscriptions_stripe_customer", "subscriptions", ["stripe_customer_id"])
    op.create_index("ix_subscriptions_stripe_sub", "subscriptions", ["stripe_subscription_id"])

    # Invoices
    op.create_table(
        "invoices",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column(
            "organisation_id",
            sa.UUID(),
            sa.ForeignKey("organisations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stripe_invoice_id", sa.String(255), nullable=False, server_default=""),
        sa.Column("invoice_number", sa.String(100), nullable=False, server_default=""),
        sa.Column("amount", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="usd"),
        sa.Column("status", sa.String(50), nullable=False, server_default="paid"),
        sa.Column("pdf_url", sa.String(500), nullable=False, server_default=""),
        sa.Column("invoice_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_invoices_org_created", "invoices", ["organisation_id", "created_at"])
    op.create_index("ix_invoices_stripe_invoice", "invoices", ["stripe_invoice_id"])

    # RLS Policies
    for table in ["subscriptions", "invoices"]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation_policy ON {table}
            USING (
                NULLIF(current_setting('app.current_organisation_id', true), '') IS NULL
                OR organisation_id = NULLIF(current_setting('app.current_organisation_id', true), '')::uuid
            )
            WITH CHECK (
                NULLIF(current_setting('app.current_organisation_id', true), '') IS NULL
                OR organisation_id = NULLIF(current_setting('app.current_organisation_id', true), '')::uuid
            );
            """
        )


def downgrade() -> None:
    for table in ["subscriptions", "invoices"]:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
    op.drop_table("invoices")
    op.drop_table("subscriptions")
