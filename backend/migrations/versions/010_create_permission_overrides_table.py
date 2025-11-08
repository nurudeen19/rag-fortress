"""Create permission_overrides table for temporary elevated permissions.

Revision ID: 010_create_permission_overrides_table
Revises: 009_create_user_permissions_table
Create Date: 2025-11-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010_create_permission_overrides_table'
down_revision = '009_create_user_permissions_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create permission_overrides table for temporary elevated permissions."""
    op.create_table(
        'permission_overrides',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column(
            'user_id',
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            'override_type',
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            'department_id',
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            'override_permission_level',
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            'reason',
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            'valid_from',
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            'valid_until',
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            'created_by_id',
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['department_id'],
            ['departments.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['created_by_id'],
            ['users.id'],
            ondelete='SET NULL',
        ),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for efficient querying
    op.create_index(
        'ix_permission_overrides_user_id',
        'permission_overrides',
        ['user_id'],
        unique=False,
    )
    op.create_index(
        'ix_permission_overrides_override_type',
        'permission_overrides',
        ['override_type'],
        unique=False,
    )
    op.create_index(
        'ix_permission_overrides_department_id',
        'permission_overrides',
        ['department_id'],
        unique=False,
    )
    op.create_index(
        'ix_permission_overrides_override_permission_level',
        'permission_overrides',
        ['override_permission_level'],
        unique=False,
    )
    op.create_index(
        'ix_permission_overrides_valid_from',
        'permission_overrides',
        ['valid_from'],
        unique=False,
    )
    op.create_index(
        'ix_permission_overrides_valid_until',
        'permission_overrides',
        ['valid_until'],
        unique=False,
    )
    op.create_index(
        'ix_permission_overrides_is_active',
        'permission_overrides',
        ['is_active'],
        unique=False,
    )

    # Create composite indexes
    op.create_index(
        'ix_permission_overrides_user_active',
        'permission_overrides',
        ['user_id', 'is_active'],
        unique=False,
    )
    op.create_index(
        'ix_permission_overrides_expiry',
        'permission_overrides',
        ['valid_until', 'is_active'],
        unique=False,
    )
    op.create_index(
        'ix_permission_overrides_user_type',
        'permission_overrides',
        ['user_id', 'override_type'],
        unique=False,
    )
    op.create_index(
        'ix_permission_overrides_dept_type',
        'permission_overrides',
        ['department_id', 'override_type'],
        unique=False,
    )


def downgrade() -> None:
    """Drop permission_overrides table."""
    # Drop all indexes
    op.drop_index('ix_permission_overrides_dept_type', table_name='permission_overrides')
    op.drop_index('ix_permission_overrides_user_type', table_name='permission_overrides')
    op.drop_index('ix_permission_overrides_expiry', table_name='permission_overrides')
    op.drop_index('ix_permission_overrides_user_active', table_name='permission_overrides')
    op.drop_index('ix_permission_overrides_is_active', table_name='permission_overrides')
    op.drop_index('ix_permission_overrides_valid_until', table_name='permission_overrides')
    op.drop_index('ix_permission_overrides_valid_from', table_name='permission_overrides')
    op.drop_index('ix_permission_overrides_override_permission_level', table_name='permission_overrides')
    op.drop_index('ix_permission_overrides_department_id', table_name='permission_overrides')
    op.drop_index('ix_permission_overrides_override_type', table_name='permission_overrides')
    op.drop_index('ix_permission_overrides_user_id', table_name='permission_overrides')

    # Drop table
    op.drop_table('permission_overrides')
