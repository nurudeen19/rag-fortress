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
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('user_invitations', schema=None) as batch_op:
        # Add department_id column with foreign key
        batch_op.add_column(
            sa.Column(
                'department_id',
                sa.Integer(),
                nullable=True
            )
        )
        
        # Add is_manager flag
        batch_op.add_column(
            sa.Column(
                'is_manager',
                sa.Boolean(),
                nullable=False,
                server_default=sa.false()
            )
        )
        
        # Create foreign key constraint
        batch_op.create_foreign_key(
            'fk_user_invitations_department_id',
            'departments',
            ['department_id'],
            ['id'],
            ondelete='SET NULL'
        )
        
        # Create index for department_id
        batch_op.create_index(
            'idx_user_invitations_department_id',
            ['department_id']
        )


def downgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('user_invitations', schema=None) as batch_op:
        # Drop index
        batch_op.drop_index('idx_user_invitations_department_id')
        
        # Drop foreign key constraint
        batch_op.drop_constraint('fk_user_invitations_department_id', type_='foreignkey')
        
        # Drop columns
        batch_op.drop_column('is_manager')
        batch_op.drop_column('department_id')
