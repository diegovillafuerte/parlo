"""Drop execution_traces table - removing playground feature.

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-02-04

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "k1l2m3n4o5p6"
down_revision = "j0k1l2m3n4o5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop indexes first
    op.drop_index("ix_execution_traces_conversation_id", table_name="execution_traces")
    op.drop_index("ix_execution_traces_org_created", table_name="execution_traces")
    op.drop_index("ix_execution_traces_exchange_id", table_name="execution_traces")

    # Drop the table
    op.drop_table("execution_traces")


def downgrade() -> None:
    # Recreate the table
    op.create_table(
        "execution_traces",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exchange_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trace_type", sa.String(length=50), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("input_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("output_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("trace_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_error", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Recreate indexes
    op.create_index("ix_execution_traces_exchange_id", "execution_traces", ["exchange_id"], unique=False)
    op.create_index(
        "ix_execution_traces_org_created",
        "execution_traces",
        ["organization_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_execution_traces_conversation_id",
        "execution_traces",
        ["conversation_id"],
        unique=False,
    )
