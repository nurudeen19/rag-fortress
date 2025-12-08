"""create_error_reports_table

Revision ID: 020
Revises: dbc6269d79ba
Create Date: 2025-12-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '020'
down_revision: Union[str, None] = 'dbc6269d79ba'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Create error_reports table
    op.create_table(
        'error_reports',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.String(36), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(50), nullable=False, server_default='other'),
        sa.Column('image_filename', sa.String(255), nullable=True),
        sa.Column('image_url', sa.String(512), nullable=True),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.Column('request_context', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='open'),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='SET NULL'),
    )
    
    # Create indexes
    op.create_index('ix_error_reports_user_id', 'error_reports', ['user_id'])
    op.create_index('ix_error_reports_conversation_id', 'error_reports', ['conversation_id'])
    op.create_index('ix_error_reports_status', 'error_reports', ['status'])
    op.create_index('ix_error_reports_category', 'error_reports', ['category'])
    op.create_index('ix_error_reports_created_at', 'error_reports', ['created_at'])
    op.create_index('ix_error_reports_user_status', 'error_reports', ['user_id', 'status'])
    op.create_index('ix_error_reports_status_category', 'error_reports', ['status', 'category'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_error_reports_status_category', table_name='error_reports')
    op.drop_index('ix_error_reports_user_status', table_name='error_reports')
    op.drop_index('ix_error_reports_created_at', table_name='error_reports')
    op.drop_index('ix_error_reports_category', table_name='error_reports')
    op.drop_index('ix_error_reports_status', table_name='error_reports')
    op.drop_index('ix_error_reports_conversation_id', table_name='error_reports')
    op.drop_index('ix_error_reports_user_id', table_name='error_reports')
    
    # Drop table
    op.drop_table('error_reports')
