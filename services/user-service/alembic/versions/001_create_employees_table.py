"""Create employees table

Revision ID: 001
Revises: 
Create Date: 2026-06-04 06:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create employees table in users schema."""
    op.create_table(
        'employees',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('first_name', sa.String(length=255), nullable=False),
        sa.Column('last_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('manager_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('hire_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['manager_id'], ['users.employees.id']),
        schema='users'
    )
    
    # Create indexes
    op.create_index('idx_employees_email', 'employees', ['email'], unique=True, schema='users')
    op.create_index('idx_employees_manager_id', 'employees', ['manager_id'], schema='users')
    op.create_index('idx_employees_department', 'employees', ['department'], schema='users')


def downgrade() -> None:
    """Drop employees table."""
    op.drop_index('idx_employees_department', table_name='employees', schema='users')
    op.drop_index('idx_employees_manager_id', table_name='employees', schema='users')
    op.drop_index('idx_employees_email', table_name='employees', schema='users')
    op.drop_table('employees', schema='users')
