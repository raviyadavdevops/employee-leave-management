"""Create notifications table

Revision ID: 001
Revises: 
Create Date: 2026-06-04 07:00:00

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
    """Create notifications table and status enum."""
    # Create enum type if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notification_status') THEN
                CREATE TYPE notifications.notification_status AS ENUM ('pending', 'sent', 'failed');
            END IF;
        END $$;
    """)
    
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('recipient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'sent', 'failed', name='notification_status', schema='notifications', create_type=False), nullable=False, server_default='pending'),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.String(length=10), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        schema='notifications'
    )
    
    # Create indexes
    op.create_index('idx_notifications_event_id', 'notifications', ['event_id'], unique=True, schema='notifications')
    op.create_index('idx_notifications_recipient_id', 'notifications', ['recipient_id'], schema='notifications')
    op.create_index('idx_notifications_status', 'notifications', ['status'], schema='notifications')


def downgrade() -> None:
    """Drop notifications table and enum."""
    op.drop_index('idx_notifications_status', table_name='notifications', schema='notifications')
    op.drop_index('idx_notifications_recipient_id', table_name='notifications', schema='notifications')
    op.drop_index('idx_notifications_event_id', table_name='notifications', schema='notifications')
    op.drop_table('notifications', schema='notifications')
    op.execute('DROP TYPE notifications.notification_status')
