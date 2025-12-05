"""Create password_reset_tokens table

Revision ID: 012
Revises: 011
Create Date: 2025-11-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create password_reset_tokens table
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.UniqueConstraint('token'),
    )
    
    # Create indexes
    op.create_index('idx_password_reset_tokens_user_id', 'password_reset_tokens', ['user_id'])
    op.create_index('idx_password_reset_tokens_email', 'password_reset_tokens', ['email'])
    op.create_index('idx_password_reset_tokens_token', 'password_reset_tokens', ['token'])
    op.create_index('idx_password_reset_tokens_is_used', 'password_reset_tokens', ['is_used'])
    op.create_index('idx_password_reset_tokens_expires_at', 'password_reset_tokens', ['expires_at'])
    op.create_index(
        'idx_token_email_valid',
        'password_reset_tokens',
        ['token', 'email', 'is_used', 'expires_at']
    )
    op.create_index('idx_password_reset_tokens_created_at', 'password_reset_tokens', ['created_at'])


def downgrade() -> None:
    # Drop table and indexes
    op.drop_index('idx_password_reset_tokens_created_at', table_name='password_reset_tokens')
    op.drop_index('idx_token_email_valid', table_name='password_reset_tokens')
    op.drop_index('idx_password_reset_tokens_expires_at', table_name='password_reset_tokens')
    op.drop_index('idx_password_reset_tokens_is_used', table_name='password_reset_tokens')
    op.drop_index('idx_password_reset_tokens_token', table_name='password_reset_tokens')
    op.drop_index('idx_password_reset_tokens_email', table_name='password_reset_tokens')
    op.drop_index('idx_password_reset_tokens_user_id', table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
