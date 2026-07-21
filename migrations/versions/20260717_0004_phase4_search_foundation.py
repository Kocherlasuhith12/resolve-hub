"""phase4 search foundation

Revision ID: 20260717_0004
Revises: 20260716_0003
Create Date: 2026-07-17 09:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260717_0004"
down_revision: str | None = "20260716_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "display_name_search_vector",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english', coalesce(display_name, ''))", persisted=True),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_users_display_name_search_vector",
        "users",
        ["display_name_search_vector"],
        unique=False,
        postgresql_using="gin",
    )
    op.add_column(
        "service_categories",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "setweight(to_tsvector('english', coalesce(name, '')), 'A') || "
                "setweight(to_tsvector('english', coalesce(description, '')), 'B')",
                persisted=True,
            ),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_service_categories_search_vector",
        "service_categories",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )
    op.add_column(
        "tickets",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "setweight(to_tsvector('english', coalesce(ticket_number, '')), 'A') || "
                "setweight(to_tsvector('english', coalesce(title, '')), 'A') || "
                "setweight(to_tsvector('english', coalesce(description, '')), 'B')",
                persisted=True,
            ),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_tickets_search_vector",
        "tickets",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )
    op.add_column(
        "ticket_comments",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english', coalesce(body, ''))", persisted=True),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_ticket_comments_search_vector",
        "ticket_comments",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_ticket_comments_search_vector", table_name="ticket_comments")
    op.drop_column("ticket_comments", "search_vector")
    op.drop_index("ix_tickets_search_vector", table_name="tickets")
    op.drop_column("tickets", "search_vector")
    op.drop_index("ix_service_categories_search_vector", table_name="service_categories")
    op.drop_column("service_categories", "search_vector")
    op.drop_index("ix_users_display_name_search_vector", table_name="users")
    op.drop_column("users", "display_name_search_vector")
