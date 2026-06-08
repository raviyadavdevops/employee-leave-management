"""Create users table in auth schema

Revision ID: 001
Revises: 
Create Date: 2026-06-04 05:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users table in auth schema."""
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        schema='auth'
    )
    
    # Create indexes
    op.create_index('idx_users_email', 'users', ['email'], unique=True, schema='auth')
    op.create_index('idx_users_role', 'users', ['role'], unique=False, schema='auth')


def downgrade() -> None:
    """Drop users table from auth schema."""
    op.drop_index('idx_users_role', table_name='users', schema='auth')
    op.drop_index('idx_users_email', table_name='users', schema='auth')
    op.drop_table('users', schema='auth')
