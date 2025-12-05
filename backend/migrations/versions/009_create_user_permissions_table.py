"""create_user_permissions_table

Revision ID: 009_create_user_permissions_table
Revises: 008_update_security_level_to_numbered
Create Date: 2025-11-08 00:00:00.000000

This migration:
1. Creates the user_permissions table for access control
2. Stores org-level and department-level permission levels
3. Enables granular access control for files and resources
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create user_permissions table."""
    
    op.create_table(
        'user_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        
        # User reference (unique one-to-one)
        sa.Column('user_id', sa.Integer(), nullable=False, unique=True),
        
        # Organization-wide permission level
        # 0=none, 1=public, 2=employee, 3=manager, 4=executive, 5=admin
        sa.Column('org_level_permission', sa.Integer(), nullable=False, server_default='2'),
        
        # Department-specific permission level
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('department_level_permission', sa.Integer(), nullable=True),
        
        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='SET NULL'),
        
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes
    op.create_index(
        op.f('ix_user_permissions_user_id'),
        'user_permissions',
        ['user_id'],
        unique=True
    )
    
    op.create_index(
        op.f('ix_user_permissions_org_level'),
        'user_permissions',
        ['org_level_permission'],
        unique=False
    )
    
    op.create_index(
        op.f('ix_user_permissions_department_id'),
        'user_permissions',
        ['department_id'],
        unique=False
    )
    
    op.create_index(
        op.f('ix_user_permissions_is_active'),
        'user_permissions',
        ['is_active'],
        unique=False
    )
    
    # Composite indexes for common queries
    op.create_index(
        op.f('idx_user_permissions_dept_level'),
        'user_permissions',
        ['department_id', 'department_level_permission'],
        unique=False
    )


def downgrade() -> None:
    """Drop user_permissions table."""
    
    op.drop_index(
        op.f('idx_user_permissions_dept_level'),
        table_name='user_permissions'
    )
    
    op.drop_index(
        op.f('ix_user_permissions_is_active'),
        table_name='user_permissions'
    )
    
    op.drop_index(
        op.f('ix_user_permissions_department_id'),
        table_name='user_permissions'
    )
    
    op.drop_index(
        op.f('ix_user_permissions_org_level'),
        table_name='user_permissions'
    )
    
    op.drop_index(
        op.f('ix_user_permissions_user_id'),
        table_name='user_permissions'
    )
    
    op.drop_table('user_permissions')
