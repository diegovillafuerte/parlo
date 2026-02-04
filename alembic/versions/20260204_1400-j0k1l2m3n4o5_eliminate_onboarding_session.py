"""Eliminate OnboardingSession - store onboarding state in Organization.

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-02-04 14:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "j0k1l2m3n4o5"
down_revision: Union[str, None] = "i9j0k1l2m3n4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new columns to organizations
    op.add_column(
        "organizations",
        sa.Column("onboarding_state", sa.String(50), nullable=True),
    )
    op.add_column(
        "organizations",
        sa.Column("onboarding_data", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "organizations",
        sa.Column("onboarding_conversation_context", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "organizations",
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 2. Make name nullable (for onboarding orgs without name yet)
    op.alter_column("organizations", "name", nullable=True)

    # 3. Set defaults for existing orgs (all are already completed, so set state to 'completed')
    op.execute("""
        UPDATE organizations
        SET onboarding_state = 'completed',
            onboarding_data = '{}',
            onboarding_conversation_context = '{}'
    """)

    # 4. Now make new columns NOT NULL after setting defaults
    op.alter_column("organizations", "onboarding_state", nullable=False)
    op.alter_column("organizations", "onboarding_data", nullable=False)
    op.alter_column("organizations", "onboarding_conversation_context", nullable=False)

    # 5. Drop onboarding_sessions table (no real users, no data to preserve)
    op.drop_table("onboarding_sessions")


def downgrade() -> None:
    # 1. Recreate onboarding_sessions table
    op.create_table(
        "onboarding_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("phone_number", sa.String(50), nullable=False),
        sa.Column("owner_name", sa.String(255), nullable=True),
        sa.Column("state", sa.String(50), nullable=False),
        sa.Column("collected_data", postgresql.JSONB(), nullable=False),
        sa.Column("conversation_context", postgresql.JSONB(), nullable=False),
        sa.Column("organization_id", sa.String(36), nullable=True),
        sa.Column("connection_token", sa.String(100), nullable=True),
        sa.Column("whatsapp_phone_number_id", sa.String(100), nullable=True),
        sa.Column("whatsapp_waba_id", sa.String(100), nullable=True),
        sa.Column("whatsapp_access_token", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone_number"),
        sa.UniqueConstraint("connection_token"),
    )
    op.create_index(
        "ix_onboarding_sessions_phone_number",
        "onboarding_sessions",
        ["phone_number"],
        unique=True,
    )
    op.create_index(
        "ix_onboarding_sessions_connection_token",
        "onboarding_sessions",
        ["connection_token"],
        unique=True,
    )

    # 2. Make name required again
    op.alter_column("organizations", "name", nullable=False)

    # 3. Remove new columns from organizations
    op.drop_column("organizations", "last_message_at")
    op.drop_column("organizations", "onboarding_conversation_context")
    op.drop_column("organizations", "onboarding_data")
    op.drop_column("organizations", "onboarding_state")
