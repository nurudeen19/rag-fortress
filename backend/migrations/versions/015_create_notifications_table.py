"""create notifications table

Revision ID: 015_create_notifications_table
Revises: 014_add_department_and_manager_to_invitations
Create Date: 2025-11-21
"""

from alembic import op
import sqlalchemy as sa

revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('related_file_id', sa.Integer(), sa.ForeignKey('file_uploads.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('notification_type', sa.String(length=50), nullable=True, index=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.false(), index=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), index=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), index=True),
    )
    op.create_index('idx_notifications_user_unread', 'notifications', ['user_id', 'is_read'])
    op.create_index('idx_notifications_type_created', 'notifications', ['notification_type', 'created_at'])


def downgrade() -> None:
    op.drop_index('idx_notifications_type_created', table_name='notifications')
    op.drop_index('idx_notifications_user_unread', table_name='notifications')
    op.drop_table('notifications')
