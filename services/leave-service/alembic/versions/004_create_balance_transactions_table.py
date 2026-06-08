"""Create balance_transactions table

Revision ID: 004
Revises: 003
Create Date: 2026-06-04 06:33:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create balance_transactions table and transaction_type enum."""
    # Create enum type if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transaction_type') THEN
                CREATE TYPE leaves.transaction_type AS ENUM ('allocation', 'deduction', 'refund', 'adjustment');
            END IF;
        END $$;
    """)
    
    op.create_table(
        'balance_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('balance_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_type', postgresql.ENUM('allocation', 'deduction', 'refund', 'adjustment', name='transaction_type', schema='leaves', create_type=False), nullable=False),
        sa.Column('amount', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('balance_before', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('balance_after', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('leave_request_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['balance_id'], ['leaves.leave_balances.id']),
        schema='leaves'
    )
    
    # Create index
    op.create_index('idx_balance_transactions_balance_id', 'balance_transactions', ['balance_id'], schema='leaves')
    op.create_index('idx_balance_transactions_leave_request_id', 'balance_transactions', ['leave_request_id'], schema='leaves')


def downgrade() -> None:
    """Drop balance_transactions table and enum."""
    op.drop_index('idx_balance_transactions_leave_request_id', table_name='balance_transactions', schema='leaves')
    op.drop_index('idx_balance_transactions_balance_id', table_name='balance_transactions', schema='leaves')
    op.drop_table('balance_transactions', schema='leaves')
    op.execute('DROP TYPE leaves.transaction_type')
