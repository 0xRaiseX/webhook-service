"""initial schema"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "projects",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("key_hash", sa.String(), nullable=False),
        sa.Column("scopes", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "endpoints",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("secret_enc", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("rate_limit_rps", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("endpoint_id", sa.String(), sa.ForeignKey("endpoints.id"), nullable=False),
        sa.Column("event_types", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("filters", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("confirmations", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "raw_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("chain_id", sa.String(), nullable=False),
        sa.Column("block_number", sa.Integer(), nullable=False),
        sa.Column("block_hash", sa.String(), nullable=False),
        sa.Column("tx_hash", sa.String(), nullable=False),
        sa.Column("tx_index", sa.Integer(), nullable=False),
        sa.Column("log_index", sa.Integer(), nullable=False),
        sa.Column("contract_address", sa.String(), nullable=False),
        sa.Column("topics", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_raw_events_tx", "raw_events", ["tx_hash"])
    op.create_index("ix_raw_events_block", "raw_events", ["block_number"])

    op.create_table(
        "events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("api_version", sa.String(), nullable=False),
        sa.Column("source", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("data", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("links", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("chain_id", sa.String(), nullable=False),
        sa.Column("contract_address", sa.String(), nullable=False),
        sa.Column("tx_hash", sa.String(), nullable=False),
    )
    op.create_index("ix_events_project_created", "events", ["project_id", "created"])
    op.create_index("ix_events_type_project_created", "events", ["type", "project_id", "created"])
    op.create_index("ix_events_chain_contract", "events", ["chain_id", "contract_address"])
    op.create_index("ix_events_tx_hash", "events", ["tx_hash"])

    op.create_table(
        "outbox",
        sa.Column("delivery_id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("event_id", sa.String(), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("subscription_id", sa.String(), sa.ForeignKey("subscriptions.id"), nullable=False),
        sa.Column("endpoint_id", sa.String(), sa.ForeignKey("endpoints.id"), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False, default=0),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, default="pending"),
        sa.Column("payload_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_outbox_next_attempt",
        "outbox",
        ["next_attempt_at"],
        postgresql_where=sa.text("status = 'pending'"),
    )

    op.create_table(
        "delivery_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("delivery_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("outbox.delivery_id")),
        sa.Column("event_id", sa.String(), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("endpoint_id", sa.String(), sa.ForeignKey("endpoints.id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_delivery_attempts_event", "delivery_attempts", ["event_id"])

    op.create_table(
        "chain_state",
        sa.Column("chain_id", sa.String(), primary_key=True),
        sa.Column("last_scanned_block", sa.Integer(), nullable=False),
        sa.Column("last_finalized_block", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("chain_state")
    op.drop_index("ix_delivery_attempts_event", table_name="delivery_attempts")
    op.drop_table("delivery_attempts")
    op.drop_index("ix_outbox_next_attempt", table_name="outbox")
    op.drop_table("outbox")
    op.drop_index("ix_events_tx_hash", table_name="events")
    op.drop_index("ix_events_chain_contract", table_name="events")
    op.drop_index("ix_events_type_project_created", table_name="events")
    op.drop_index("ix_events_project_created", table_name="events")
    op.drop_table("events")
    op.drop_index("ix_raw_events_block", table_name="raw_events")
    op.drop_index("ix_raw_events_tx", table_name="raw_events")
    op.drop_table("raw_events")
    op.drop_table("subscriptions")
    op.drop_table("endpoints")
    op.drop_table("api_keys")
    op.drop_table("projects")

