"""create_user_invitations_and_auth_tables

Revision ID: 005_create_user_invitations_and_auth_tables
Revises: 004_create_user_profiles_table
Create Date: 2025-11-07 00:00:00.000000

This migration:
1. Creates the user_invitations table for admin invitation tracking
2. Adds permission tracking for role-based access control
3. Updates default roles to include: admin, executive, manager, user
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "005_create_user_invitations_and_auth_tables"
down_revision: Union[str, None] = "004_create_user_profiles_table"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create user_invitations table and update auth system."""
    
    # Create user_invitations table
    op.create_table(
        'user_invitations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('invited_by_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('invitation_message', sa.Text(), nullable=True),
        sa.Column('assigned_role', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['invited_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token', name=op.f('uq_user_invitations_token')),
    )
    
    op.create_index(op.f('ix_invitation_email'), 'user_invitations', ['email'], unique=False)
    op.create_index(op.f('ix_invitation_token'), 'user_invitations', ['token'], unique=True)
    op.create_index(op.f('ix_invitation_status'), 'user_invitations', ['status'], unique=False)
    op.create_index(op.f('ix_invitation_expires_at'), 'user_invitations', ['expires_at'], unique=False)
    
    # Update roles to include new ones
    # First, delete old system roles
    op.execute("DELETE FROM role_permissions WHERE role_id IN (SELECT id FROM roles WHERE is_system = 1)")
    op.execute("DELETE FROM user_roles WHERE role_id IN (SELECT id FROM roles WHERE is_system = 1)")
    op.execute("DELETE FROM roles WHERE is_system = 1")
    
    # Insert new system roles
    roles_table = sa.table(
        'roles',
        sa.column('name'),
        sa.column('description'),
        sa.column('is_system'),
        sa.column('created_at'),
        sa.column('updated_at'),
    )
    
    op.bulk_insert(
        roles_table,
        [
            {
                'name': 'admin',
                'description': 'Administrator with full access',
                'is_system': True,
                'created_at': sa.func.now(),
                'updated_at': sa.func.now(),
            },
            {
                'name': 'executive',
                'description': 'Executive with strategic access',
                'is_system': True,
                'created_at': sa.func.now(),
                'updated_at': sa.func.now(),
            },
            {
                'name': 'manager',
                'description': 'Manager with team oversight access',
                'is_system': True,
                'created_at': sa.func.now(),
                'updated_at': sa.func.now(),
            },
            {
                'name': 'user',
                'description': 'Regular user with standard access',
                'is_system': True,
                'created_at': sa.func.now(),
                'updated_at': sa.func.now(),
            },
        ]
    )


def downgrade() -> None:
    """Revert user_invitations table and auth updates."""
    
    # Drop user_invitations table
    op.drop_index(op.f('ix_invitation_expires_at'), table_name='user_invitations')
    op.drop_index(op.f('ix_invitation_status'), table_name='user_invitations')
    op.drop_index(op.f('ix_invitation_token'), table_name='user_invitations')
    op.drop_index(op.f('ix_invitation_email'), table_name='user_invitations')
    op.drop_table('user_invitations')
    
    # Restore old roles
    op.execute("DELETE FROM role_permissions WHERE role_id IN (SELECT id FROM roles WHERE is_system = 1)")
    op.execute("DELETE FROM user_roles WHERE role_id IN (SELECT id FROM roles WHERE is_system = 1)")
    op.execute("DELETE FROM roles WHERE is_system = 1")
    
    roles_table = sa.table(
        'roles',
        sa.column('name'),
        sa.column('description'),
        sa.column('is_system'),
        sa.column('created_at'),
        sa.column('updated_at'),
    )
    
    op.bulk_insert(
        roles_table,
        [
            {
                'name': 'admin',
                'description': 'Administrator with full access',
                'is_system': True,
                'created_at': sa.func.now(),
                'updated_at': sa.func.now(),
            },
            {
                'name': 'user',
                'description': 'Regular user with basic access',
                'is_system': True,
                'created_at': sa.func.now(),
                'updated_at': sa.func.now(),
            },
            {
                'name': 'viewer',
                'description': 'Read-only access',
                'is_system': True,
                'created_at': sa.func.now(),
                'updated_at': sa.func.now(),
            },
        ]
    )
