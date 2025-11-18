"""Add department_id and is_manager to user_invitations table

Revision ID: 014
Revises: 013
Create Date: 2025-11-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add department_id column with foreign key
    op.add_column(
        'user_invitations',
        sa.Column(
            'department_id',
            sa.Integer(),
            nullable=True,
            comment='Department to assign user to during onboarding'
        )
    )
    
    # Add is_manager flag
    op.add_column(
        'user_invitations',
        sa.Column(
            'is_manager',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment='Whether to make user a manager of assigned department'
        )
    )
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_user_invitations_department_id',
        'user_invitations',
        'departments',
        ['department_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Create index for department_id
    op.create_index(
        'idx_user_invitations_department_id',
        'user_invitations',
        ['department_id']
    )


def downgrade() -> None:
    # Drop index
    op.drop_index(
        'idx_user_invitations_department_id',
        table_name='user_invitations'
    )
    
    # Drop foreign key constraint
    op.drop_constraint(
        'fk_user_invitations_department_id',
        'user_invitations',
        type_='foreignkey'
    )
    
    # Drop columns
    op.drop_column('user_invitations', 'is_manager')
    op.drop_column('user_invitations', 'department_id')
