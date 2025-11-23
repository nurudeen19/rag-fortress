"""create conversations and messages tables

Revision ID: 016_create_conversations_and_messages_tables
Revises: 015_create_notifications_table
Create Date: 2025-11-23
"""

from alembic import op
import sqlalchemy as sa

revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('last_message_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), index=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('0'), index=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_conv_user_deleted', 'conversations', ['user_id', 'is_deleted'])
    op.create_index('idx_conv_user_updated', 'conversations', ['user_id', 'last_message_at'])

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('conversation_id', sa.String(length=36), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('role', sa.Enum('USER', 'ASSISTANT', 'SYSTEM', name='messagerole'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_msg_conv_created', 'messages', ['conversation_id', 'created_at'])
    op.create_index('idx_msg_role', 'messages', ['role'])


def downgrade() -> None:
    # Drop messages table
    op.drop_index('idx_msg_role', table_name='messages')
    op.drop_index('idx_msg_conv_created', table_name='messages')
    op.drop_table('messages')
    
    # Drop conversations table
    op.drop_index('idx_conv_user_updated', table_name='conversations')
    op.drop_index('idx_conv_user_deleted', table_name='conversations')
    op.drop_table('conversations')
