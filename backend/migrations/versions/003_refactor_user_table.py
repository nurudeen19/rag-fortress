"""refactor_user_table

Revision ID: 003_refactor_user_table
Revises: 002_create_user_management
Create Date: 2025-11-07 00:00:00.000000

This migration:
1. Separates full_name into first_name and last_name
2. Adds account suspension fields (is_suspended, suspension_reason, suspended_at)
3. Drops the old full_name and bio columns
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "003_refactor_user_table"
down_revision: Union[str, None] = "002_create_user_management"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Apply user table refactoring."""
    
    # Add new columns to users table
    op.add_column('users', sa.Column('first_name', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('is_suspended', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('suspension_reason', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('suspended_at', sa.DateTime(), nullable=True))
    
    # Migrate full_name to first_name and last_name if data exists
    op.execute("""
        UPDATE users
        SET 
            first_name = CASE 
                WHEN full_name IS NOT NULL THEN 
                    SUBSTR(full_name, 1, INSTR(full_name || ' ', ' ') - 1)
                ELSE 'Unknown'
            END,
            last_name = CASE 
                WHEN full_name IS NOT NULL AND INSTR(full_name, ' ') > 0 THEN
                    SUBSTR(full_name, INSTR(full_name, ' ') + 1)
                ELSE ''
            END
        WHERE full_name IS NOT NULL
    """)
    
    # Set NOT NULL constraint for first_name and last_name
    op.alter_column('users', 'first_name', existing_type=sa.String(length=100), nullable=False)
    op.alter_column('users', 'last_name', existing_type=sa.String(length=100), nullable=False)
    
    # Drop old columns
    op.drop_column('users', 'full_name')
    op.drop_column('users', 'bio')
    
    # Create is_suspended index
    op.create_index(
        op.f('ix_users_is_suspended'),
        'users',
        ['is_suspended'],
        unique=False
    )


def downgrade() -> None:
    """Revert user table refactoring."""
    
    # Drop is_suspended index
    op.drop_index(op.f('ix_users_is_suspended'), table_name='users')
    
    # Restore old columns
    op.add_column('users', sa.Column('bio', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('full_name', sa.String(length=255), nullable=True))
    
    # Migrate first_name and last_name back to full_name
    op.execute("""
        UPDATE users
        SET full_name = TRIM(first_name || ' ' || last_name)
    """)
    
    # Drop new columns
    op.drop_column('users', 'suspended_at')
    op.drop_column('users', 'suspension_reason')
    op.drop_column('users', 'is_suspended')
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
