"""add uniqueness and chain_state hash"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_correctness_constraints"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("chain_state", sa.Column("last_block_hash", sa.String(), nullable=True))
    op.create_unique_constraint(
        "uq_raw_events_unique", "raw_events", ["chain_id", "tx_hash", "log_index"]
    )
    op.create_unique_constraint(
        "uq_outbox_event_sub", "outbox", ["event_id", "subscription_id"]
    )


def downgrade():
    op.drop_constraint("uq_outbox_event_sub", "outbox", type_="unique")
    op.drop_constraint("uq_raw_events_unique", "raw_events", type_="unique")
    op.drop_column("chain_state", "last_block_hash")

