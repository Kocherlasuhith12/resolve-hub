"""phase5 browser sessions

Revision ID: 20260718_0006
Revises: 20260717_0005
Create Date: 2026-07-18 09:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260718_0006"
down_revision: str | None = "20260717_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("auth_sessions", sa.Column("csrf_token_hash", sa.String(length=64)))


def downgrade() -> None:
    op.drop_column("auth_sessions", "csrf_token_hash")
