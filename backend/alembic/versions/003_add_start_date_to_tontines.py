"""Add start_date to tontines

Revision ID: 003
Revises: 002
Create Date: 2026-03-09
"""

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tontines", sa.Column("start_date", sa.Date, nullable=True))


def downgrade() -> None:
    op.drop_column("tontines", "start_date")
