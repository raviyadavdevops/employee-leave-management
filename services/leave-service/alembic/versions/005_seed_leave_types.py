"""Seed leave types

Revision ID: 005
Revises: 004
Create Date: 2026-06-04 06:34:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed default leave types (annual, sick, personal)."""
    op.execute("""
        INSERT INTO leaves.leave_types (name, display_name, default_allocation, requires_approval, is_active)
        VALUES
            ('annual', 'Annual Leave', 20.00, true, true),
            ('sick', 'Sick Leave', 10.00, false, true),
            ('personal', 'Personal Leave', 5.00, true, true)
        ON CONFLICT (name) DO NOTHING;
    """)


def downgrade() -> None:
    """Remove seeded leave types."""
    op.execute("""
        DELETE FROM leaves.leave_types
        WHERE name IN ('annual', 'sick', 'personal');
    """)
