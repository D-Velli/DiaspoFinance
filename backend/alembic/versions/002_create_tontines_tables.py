"""Create tontines and tontine_members tables

Revision ID: 002
Revises: 001
Create Date: 2026-03-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tontines",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("hand_amount_cents", sa.BigInteger, nullable=False),
        sa.Column(
            "frequency",
            sa.Enum("weekly", "biweekly", "monthly", name="tontinefrequency"),
            nullable=False,
        ),
        sa.Column("max_members", sa.Integer, nullable=True),
        sa.Column("max_pot_cents", sa.BigInteger, nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "draft", "active", "collecting", "distributing", "completed", "cancelled",
                name="tontinestatus",
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("reserve_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("reserve_percentage", sa.Numeric(4, 2), nullable=True),
        sa.Column("invite_code", sa.String, unique=True, nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="CAD"),
        sa.Column("created_at", TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "tontine_members",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "tontine_id", UUID(as_uuid=True), sa.ForeignKey("tontines.id"), nullable=False
        ),
        sa.Column(
            "role",
            sa.Enum("organizer", "member", name="memberrole"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("invited", "preview", "active", "suspended", "exited", name="memberstatus"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("hands", sa.Numeric(2, 1), nullable=False, server_default="1"),
        sa.Column("turn_position", sa.Integer, nullable=True),
        sa.Column("joined_at", TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "tontine_id"),
    )


def downgrade() -> None:
    op.drop_table("tontine_members")
    op.drop_table("tontines")
    op.execute("DROP TYPE IF EXISTS memberrole")
    op.execute("DROP TYPE IF EXISTS memberstatus")
    op.execute("DROP TYPE IF EXISTS tontinestatus")
    op.execute("DROP TYPE IF EXISTS tontinefrequency")
