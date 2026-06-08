"""Create leave_requests table

Revision ID: 003
Revises: 002
Create Date: 2026-06-04 06:32:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create leave_requests table and status enum."""
    # Create enum type if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'leave_request_status') THEN
                CREATE TYPE leaves.leave_request_status AS ENUM ('pending', 'approved', 'rejected', 'cancelled');
            END IF;
        END $$;
    """)
    
    op.create_table(
        'leave_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('leave_type_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('days_requested', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', postgresql.ENUM('pending', 'approved', 'rejected', 'cancelled', name='leave_request_status', schema='leaves', create_type=False), nullable=False, server_default='pending'),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['leave_type_id'], ['leaves.leave_types.id']),
        schema='leaves'
    )
    
    # Create indexes
    op.create_index('idx_leave_requests_employee_id', 'leave_requests', ['employee_id'], schema='leaves')
    op.create_index('idx_leave_requests_status', 'leave_requests', ['status'], schema='leaves')
    op.create_index('idx_leave_requests_dates', 'leave_requests', ['start_date', 'end_date'], schema='leaves')


def downgrade() -> None:
    """Drop leave_requests table and enum."""
    op.drop_index('idx_leave_requests_dates', table_name='leave_requests', schema='leaves')
    op.drop_index('idx_leave_requests_status', table_name='leave_requests', schema='leaves')
    op.drop_index('idx_leave_requests_employee_id', table_name='leave_requests', schema='leaves')
    op.drop_table('leave_requests', schema='leaves')
    op.execute('DROP TYPE leaves.leave_request_status')
