"""create activity_logs table

Revision ID: 017_create_activity_logs_table
Revises: 016_create_conversations_and_messages_tables
Create Date: 2025-11-24
"""

from alembic import op
import sqlalchemy as sa

revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create activity_logs table
    op.create_table(
        'activity_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('incident_type', sa.String(length=100), nullable=False, index=True),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='info', index=True),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('user_clearance_level', sa.String(length=50), nullable=True),
        sa.Column('required_clearance_level', sa.String(length=50), nullable=True),
        sa.Column('access_granted', sa.Boolean(), nullable=True, index=True),
        sa.Column('user_query', sa.Text(), nullable=True),
        sa.Column('threat_type', sa.String(length=100), nullable=True),
        sa.Column('conversation_id', sa.String(length=36), sa.ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
    )
    
    # Create composite indexes for performance
    op.create_index('idx_activity_user_type', 'activity_logs', ['user_id', 'incident_type'])
    op.create_index('idx_activity_user_created', 'activity_logs', ['user_id', 'created_at'])
    op.create_index('idx_activity_severity_created', 'activity_logs', ['severity', 'created_at'])
    op.create_index('idx_activity_type_created', 'activity_logs', ['incident_type', 'created_at'])
    op.create_index('idx_activity_access_denied', 'activity_logs', ['user_id', 'access_granted', 'created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_activity_access_denied', table_name='activity_logs')
    op.drop_index('idx_activity_type_created', table_name='activity_logs')
    op.drop_index('idx_activity_severity_created', table_name='activity_logs')
    op.drop_index('idx_activity_user_created', table_name='activity_logs')
    op.drop_index('idx_activity_user_type', table_name='activity_logs')
    
    # Drop table
    op.drop_table('activity_logs')
