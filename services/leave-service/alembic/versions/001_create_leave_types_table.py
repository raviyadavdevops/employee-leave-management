"""Create leave_types table

Revision ID: 001
Revises: 
Create Date: 2026-06-04 06:30:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create leave_types table in leaves schema."""
    op.create_table(
        'leave_types',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('default_allocation', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('requires_approval', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.PrimaryKeyConstraint('id'),
        schema='leaves'
    )
    
    # Create unique index on name
    op.create_index('idx_leave_types_name', 'leave_types', ['name'], unique=True, schema='leaves')


def downgrade() -> None:
    """Drop leave_types table."""
    op.drop_index('idx_leave_types_name', table_name='leave_types', schema='leaves')
    op.drop_table('leave_types', schema='leaves')
