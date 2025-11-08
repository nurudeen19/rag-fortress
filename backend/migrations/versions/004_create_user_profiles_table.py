"""create_user_profiles_table

Revision ID: 004_create_user_profiles_table
Revises: 003_refactor_user_table
Create Date: 2025-11-07 00:00:00.000000

This migration:
1. Creates the user_profiles table for extended profile information
2. Supports bio, about, avatar, contact info, professional info, and preferences
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create user_profiles table."""
    
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('about', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('job_title', sa.String(length=255), nullable=True),
        sa.Column('department', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name=op.f('uq_user_profiles_user_id')),
    )
    
    op.create_index(
        op.f('ix_user_profile_user_id'),
        'user_profiles',
        ['user_id'],
        unique=False
    )


def downgrade() -> None:
    """Drop user_profiles table."""
    
    op.drop_index(op.f('ix_user_profile_user_id'), table_name='user_profiles')
    op.drop_table('user_profiles')
