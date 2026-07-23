"""phase7 rls storage observability

Revision ID: 20260721_0008
Revises: 20260721_0007
Create Date: 2026-07-21 15:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260721_0008"
down_revision: str | None = "20260721_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TENANT_TABLES = [
    "memberships",
    "departments",
    "service_categories",
    "tickets",
    "ticket_events",
    "ticket_comments",
    "attachments",
    "sla_policies",
    "business_calendars",
    "calendar_holidays",
    "notifications",
    "ai_assistance_runs",
    "ai_suggestions",
    "api_keys",
    "webhook_subscriptions",
    "webhook_deliveries",
    "idempotency_records",
    "outbox_records",
]


def upgrade() -> None:
    for table in TENANT_TABLES:
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
    for table in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
