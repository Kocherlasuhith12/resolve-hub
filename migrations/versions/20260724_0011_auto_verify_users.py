"""auto verify registered users

Revision ID: 20260724_0011
Revises: 20260723_0010
Create Date: 2026-07-24 12:30:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260724_0011"
down_revision: str | None = "20260723_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE users SET is_email_verified = true WHERE is_email_verified = false")


def downgrade() -> None:
    pass
