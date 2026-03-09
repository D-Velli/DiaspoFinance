"""create tontine_rounds table and add cycle columns to tontines

Revision ID: 005
Revises: 004
Create Date: 2026-03-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns to tontines
    op.add_column("tontines", sa.Column("order_locked_at", TIMESTAMP(timezone=True), nullable=True))
    op.add_column("tontines", sa.Column("cycle_start_date", sa.Date(), nullable=True))

    # Create enum and table via raw SQL to avoid asyncpg checkfirst issues
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE roundstatus AS ENUM ('pending', 'collecting', 'complete', 'paused', 'cancelled');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        CREATE TABLE tontine_rounds (
            id UUID PRIMARY KEY,
            tontine_id UUID NOT NULL REFERENCES tontines(id),
            round_number INTEGER NOT NULL,
            beneficiary_user_id UUID NOT NULL REFERENCES users(id),
            beneficiary_hands NUMERIC(2, 1) NOT NULL,
            expected_collection_date DATE NOT NULL,
            expected_distribution_date DATE NOT NULL,
            status roundstatus NOT NULL DEFAULT 'pending',
            pot_expected_amount_cents BIGINT NOT NULL,
            pot_actual_amount_cents BIGINT,
            created_at TIMESTAMPTZ DEFAULT now(),
            UNIQUE (tontine_id, round_number)
        );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tontine_rounds")
    op.execute("DROP TYPE IF EXISTS roundstatus")
    op.drop_column("tontines", "cycle_start_date")
    op.drop_column("tontines", "order_locked_at")
