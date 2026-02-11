"""add appointment overlap exclusion constraints

Revision ID: f3a4b5c6d7e8
Revises: l2m3n4o5p6q7
Create Date: 2026-02-11 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3a4b5c6d7e8"
down_revision: Union[str, None] = "l2m3n4o5p6q7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add exclusion constraints to prevent overlapping appointments."""
    # Enable required extension for exclusion constraints
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    # Staff overlap constraint
    op.execute(
        """
        ALTER TABLE appointments
        ADD CONSTRAINT no_overlapping_staff_appointments
        EXCLUDE USING gist (
            organization_id WITH =,
            parlo_user_id WITH =,
            tstzrange(scheduled_start, scheduled_end, '[)') WITH &&
        )
        WHERE (
            parlo_user_id IS NOT NULL
            AND status IN ('pending', 'confirmed')
        )
        """
    )

    # Spot overlap constraint
    op.execute(
        """
        ALTER TABLE appointments
        ADD CONSTRAINT no_overlapping_spot_appointments
        EXCLUDE USING gist (
            organization_id WITH =,
            spot_id WITH =,
            tstzrange(scheduled_start, scheduled_end, '[)') WITH &&
        )
        WHERE (
            spot_id IS NOT NULL
            AND status IN ('pending', 'confirmed')
        )
        """
    )


def downgrade() -> None:
    """Remove exclusion constraints."""
    op.execute(
        "ALTER TABLE appointments DROP CONSTRAINT IF EXISTS no_overlapping_spot_appointments"
    )
    op.execute(
        "ALTER TABLE appointments DROP CONSTRAINT IF EXISTS no_overlapping_staff_appointments"
    )
