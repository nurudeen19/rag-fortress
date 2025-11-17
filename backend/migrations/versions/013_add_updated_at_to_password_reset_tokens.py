"""Add updated_at column to password_reset_tokens table

Revision ID: 013
Revises: 012
Create Date: 2025-11-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add updated_at column to password_reset_tokens table
    op.add_column('password_reset_tokens', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    
    # Create index for updated_at
    op.create_index('idx_password_reset_tokens_updated_at', 'password_reset_tokens', ['updated_at'])


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_password_reset_tokens_updated_at', table_name='password_reset_tokens')
    
    # Drop column
    op.drop_column('password_reset_tokens', 'updated_at')

