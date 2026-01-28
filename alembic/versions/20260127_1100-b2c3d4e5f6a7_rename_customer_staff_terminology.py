"""rename customer and staff terminology

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-27 11:00:00.000000

Renames:
- customers table -> end_customers
- staff table -> yume_users
- staff_service_types table -> yume_user_service_types
- Related columns: customer_id -> end_customer_id, staff_id -> yume_user_id
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema - rename customer/staff terminology."""

    # Step 1: Rename the main tables
    op.rename_table('customers', 'end_customers')
    op.rename_table('staff', 'yume_users')
    op.rename_table('staff_service_types', 'yume_user_service_types')

    # Step 2: Rename indexes on the renamed tables (wrapped in try/except for resilience)
    from sqlalchemy import text
    conn = op.get_bind()

    # customers -> end_customers indexes
    try:
        conn.execute(text('ALTER INDEX ix_customer_phone_number RENAME TO ix_end_customer_phone_number'))
    except Exception:
        pass  # Index might not exist or have different name

    # staff -> yume_users indexes
    try:
        conn.execute(text('ALTER INDEX ix_staff_phone_number RENAME TO ix_yume_user_phone_number'))
    except Exception:
        pass  # Index might not exist or have different name

    # Step 3: Rename columns in appointments table
    op.alter_column('appointments', 'customer_id', new_column_name='end_customer_id')
    op.alter_column('appointments', 'staff_id', new_column_name='yume_user_id')

    # Step 4: Rename columns in conversations table
    op.alter_column('conversations', 'customer_id', new_column_name='end_customer_id')

    # Step 5: Rename columns in availability table
    op.alter_column('availability', 'staff_id', new_column_name='yume_user_id')

    # Step 6: Rename column in yume_user_service_types (association table)
    op.alter_column('yume_user_service_types', 'staff_id', new_column_name='yume_user_id')

    # Step 7: Rename constraints (wrapped in try/except for resilience)
    # The constraint names might vary depending on how they were created
    from sqlalchemy import text
    conn = op.get_bind()

    # Try to rename customers unique constraint
    try:
        conn.execute(text('ALTER TABLE end_customers RENAME CONSTRAINT uq_customer_org_phone TO uq_end_customer_org_phone'))
    except Exception:
        pass  # Constraint might not exist or have different name

    # Try to rename staff unique constraint
    try:
        conn.execute(text('ALTER TABLE yume_users RENAME CONSTRAINT uq_staff_org_phone TO uq_yume_user_org_phone'))
    except Exception:
        pass  # Constraint might not exist or have different name


def downgrade() -> None:
    """Downgrade database schema - revert customer/staff terminology."""
    from sqlalchemy import text
    conn = op.get_bind()

    # Step 1: Rename constraints back (wrapped in try/except for resilience)
    try:
        conn.execute(text('ALTER TABLE end_customers RENAME CONSTRAINT uq_end_customer_org_phone TO uq_customer_org_phone'))
    except Exception:
        pass
    try:
        conn.execute(text('ALTER TABLE yume_users RENAME CONSTRAINT uq_yume_user_org_phone TO uq_staff_org_phone'))
    except Exception:
        pass

    # Step 2: Rename columns back
    op.alter_column('yume_user_service_types', 'yume_user_id', new_column_name='staff_id')
    op.alter_column('availability', 'yume_user_id', new_column_name='staff_id')
    op.alter_column('conversations', 'end_customer_id', new_column_name='customer_id')
    op.alter_column('appointments', 'yume_user_id', new_column_name='staff_id')
    op.alter_column('appointments', 'end_customer_id', new_column_name='customer_id')

    # Step 3: Rename indexes back (wrapped in try/except for resilience)
    try:
        conn.execute(text('ALTER INDEX ix_yume_user_phone_number RENAME TO ix_staff_phone_number'))
    except Exception:
        pass
    try:
        conn.execute(text('ALTER INDEX ix_end_customer_phone_number RENAME TO ix_customer_phone_number'))
    except Exception:
        pass

    # Step 4: Rename tables back
    op.rename_table('yume_user_service_types', 'staff_service_types')
    op.rename_table('yume_users', 'staff')
    op.rename_table('end_customers', 'customers')
