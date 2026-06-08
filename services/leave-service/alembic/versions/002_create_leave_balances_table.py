"""Create leave_balances table

Revision ID: 002
Revises: 001
Create Date: 2026-06-04 06:31:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create leave_balances table in leaves schema."""
    op.create_table(
        'leave_balances',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('leave_type_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('total_allocated', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('available', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('provisional', sa.Numeric(precision=5, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('consumed', sa.Numeric(precision=5, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['leave_type_id'], ['leaves.leave_types.id']),
        schema='leaves'
    )
    
    # Create indexes
    op.create_index('idx_leave_balances_employee_id', 'leave_balances', ['employee_id'], schema='leaves')
    op.create_index('idx_leave_balances_employee_type_year', 'leave_balances', ['employee_id', 'leave_type_id', 'year'], unique=True, schema='leaves')


def downgrade() -> None:
    """Drop leave_balances table."""
    op.drop_index('idx_leave_balances_employee_type_year', table_name='leave_balances', schema='leaves')
    op.drop_index('idx_leave_balances_employee_id', table_name='leave_balances', schema='leaves')
    op.drop_table('leave_balances', schema='leaves')
