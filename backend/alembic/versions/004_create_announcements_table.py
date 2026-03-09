"""create announcements table

Revision ID: 004
Revises: 003
Create Date: 2026-03-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "announcements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tontine_id", UUID(as_uuid=True), sa.ForeignKey("tontines.id"), nullable=False),
        sa.Column("author_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_announcements_tontine_created",
        "announcements",
        ["tontine_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "ix_announcements_author_created",
        "announcements",
        ["author_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_announcements_author_created", table_name="announcements")
    op.drop_index("ix_announcements_tontine_created", table_name="announcements")
    op.drop_table("announcements")
