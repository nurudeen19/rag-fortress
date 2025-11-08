"""create_user_management_tables

Revision ID: 002_create_user_management
Revises: 001_create_application_settings
Create Date: 2025-11-07 00:00:00.000000

This migration creates all tables related to user management:
- users: Main user table with authentication info
- roles: Role definitions for RBAC
- permissions: Fine-grained permissions
- user_roles: Association table for users and roles
- role_permissions: Association table for roles and permissions
"""
from typing import Sequence, Union
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create user management tables."""
    
    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name=op.f('uq_roles_name')),
    )
    
    # Create indexes for roles
    op.create_index(
        op.f('ix_roles_name'),
        'roles',
        ['name'],
        unique=True
    )
    
    # Create permissions table
    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('code', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('resource', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name=op.f('uq_permissions_code')),
    )
    
    # Create indexes for permissions
    op.create_index(
        op.f('ix_permissions_code'),
        'permissions',
        ['code'],
        unique=True
    )
    op.create_index(
        op.f('ix_permissions_resource'),
        'permissions',
        ['resource'],
        unique=False
    )
    op.create_index(
        op.f('ix_permissions_resource_action'),
        'permissions',
        ['resource', 'action'],
        unique=False
    )
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username', name=op.f('uq_users_username')),
        sa.UniqueConstraint('email', name=op.f('uq_users_email')),
    )
    
    # Create indexes for users
    op.create_index(
        op.f('ix_users_username'),
        'users',
        ['username'],
        unique=True
    )
    op.create_index(
        op.f('ix_users_email'),
        'users',
        ['email'],
        unique=True
    )
    op.create_index(
        op.f('ix_users_is_active'),
        'users',
        ['is_active'],
        unique=False
    )
    op.create_index(
        op.f('ix_users_created_at'),
        'users',
        ['created_at'],
        unique=False
    )
    
    # Create user_roles association table
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id'),
    )
    
    # Create role_permissions association table
    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id'),
    )
    
    # Insert default roles
    roles_table = sa.table(
        'roles',
        sa.column('name'),
        sa.column('description'),
        sa.column('is_system'),
        sa.column('created_at'),
        sa.column('updated_at'),
    )
    
    now = datetime.now(timezone.utc)
    
    op.bulk_insert(
        roles_table,
        [
            {
                'name': 'admin',
                'description': 'Administrator with full access',
                'is_system': True,
                'created_at': now,
                'updated_at': now,
            },
            {
                'name': 'user',
                'description': 'Regular user with basic access',
                'is_system': True,
                'created_at': now,
                'updated_at': now,
            },
            {
                'name': 'viewer',
                'description': 'Read-only access',
                'is_system': True,
                'created_at': now,
                'updated_at': now,
            },
        ]
    )
    
    # Insert default permissions
    permissions_table = sa.table(
        'permissions',
        sa.column('code'),
        sa.column('description'),
        sa.column('resource'),
        sa.column('action'),
        sa.column('created_at'),
        sa.column('updated_at'),
    )
    
    op.bulk_insert(
        permissions_table,
        [
            # User permissions
            {
                'code': 'user:create',
                'description': 'Create new users',
                'resource': 'user',
                'action': 'create',
                'created_at': now,
                'updated_at': now,
            },
            {
                'code': 'user:read',
                'description': 'Read user information',
                'resource': 'user',
                'action': 'read',
                'created_at': now,
                'updated_at': now,
            },
            {
                'code': 'user:update',
                'description': 'Update user information',
                'resource': 'user',
                'action': 'update',
                'created_at': now,
                'updated_at': now,
            },
            {
                'code': 'user:delete',
                'description': 'Delete users',
                'resource': 'user',
                'action': 'delete',
                'created_at': now,
                'updated_at': now,
            },
            # Document permissions
            {
                'code': 'document:create',
                'description': 'Upload and create documents',
                'resource': 'document',
                'action': 'create',
                'created_at': now,
                'updated_at': now,
            },
            {
                'code': 'document:read',
                'description': 'Read and view documents',
                'resource': 'document',
                'action': 'read',
                'created_at': now,
                'updated_at': now,
            },
            {
                'code': 'document:update',
                'description': 'Update document metadata',
                'resource': 'document',
                'action': 'update',
                'created_at': now,
                'updated_at': now,
            },
            {
                'code': 'document:delete',
                'description': 'Delete documents',
                'resource': 'document',
                'action': 'delete',
                'created_at': now,
                'updated_at': now,
            },
            # Settings permissions
            {
                'code': 'settings:read',
                'description': 'Read application settings',
                'resource': 'settings',
                'action': 'read',
                'created_at': now,
                'updated_at': now,
            },
            {
                'code': 'settings:update',
                'description': 'Update application settings',
                'resource': 'settings',
                'action': 'update',
                'created_at': now,
                'updated_at': now,
            },
        ]
    )


def downgrade() -> None:
    """Drop user management tables."""
    op.drop_table('role_permissions')
    op.drop_table('user_roles')
    op.drop_index(op.f('ix_users_created_at'), table_name='users')
    op.drop_index(op.f('ix_users_is_active'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_permissions_resource_action'), table_name='permissions')
    op.drop_index(op.f('ix_permissions_resource'), table_name='permissions')
    op.drop_index(op.f('ix_permissions_code'), table_name='permissions')
    op.drop_table('permissions')
    op.drop_index(op.f('ix_roles_name'), table_name='roles')
    op.drop_table('roles')
