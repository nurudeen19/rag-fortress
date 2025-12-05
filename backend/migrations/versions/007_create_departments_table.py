"""create_departments_table

Revision ID: 007_create_departments_table
Revises: 006_create_file_uploads_table
Create Date: 2025-11-08 00:00:00.000000

This migration:
1. Creates the departments table for organizational structure
2. Adds department_id to users table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '005'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create departments table and add department_id to users."""
    
    # Create departments table
    op.create_table(
        'departments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        
        # Department information
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
                
        # Department metadata
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        
        # Department head (manager)
        sa.Column('manager_id', sa.Integer(), nullable=True),
                
        # Foreign keys
        sa.ForeignKeyConstraint(['manager_id'], ['users.id'], ondelete='SET NULL'),
        
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes
    op.create_index(
        op.f('ix_department_name'),
        'departments',
        ['name'],
        unique=False
    )
    
    op.create_index(
        op.f('ix_department_code'),
        'departments',
        ['code'],
        unique=False
    )
    
    op.create_index(
        op.f('ix_department_is_active'),
        'departments',
        ['is_active'],
        unique=False
    )
    
    op.create_index(
        op.f('ix_department_created_at'),
        'departments',
        ['created_at'],
        unique=False
    )
    
    # Add department_id to users table
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('department_id', sa.Integer(), nullable=True))
        batch_op.create_index(
            op.f('ix_users_department_id'),
            ['department_id'],
            unique=False
        )
        batch_op.create_foreign_key(
            op.f('fk_users_department_id'),
            'departments',
            ['department_id'],
            ['id'],
            ondelete='SET NULL'
        )


def downgrade() -> None:
    """Remove departments table and department_id from users."""
    
    # Remove foreign key and column from users using batch mode
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint(
            op.f('fk_users_department_id'),
            type_='foreignkey'
        )
        batch_op.drop_index(op.f('ix_users_department_id'))
        batch_op.drop_column('department_id')
    
    # Drop departments table indexes
    op.drop_index(op.f('idx_department_parent_active'), table_name='departments')
    op.drop_index(op.f('ix_department_created_at'), table_name='departments')
    op.drop_index(op.f('ix_department_cost_center'), table_name='departments')
    op.drop_index(op.f('ix_department_is_active'), table_name='departments')
    op.drop_index(op.f('ix_department_code'), table_name='departments')
    op.drop_index(op.f('ix_department_parent_id'), table_name='departments')
    op.drop_index(op.f('ix_department_slug'), table_name='departments')
    op.drop_index(op.f('ix_department_name'), table_name='departments')
    
    # Drop departments table
    op.drop_table('departments')
