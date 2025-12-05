"""create_file_uploads_table

Revision ID: 006_create_file_uploads_table
Revises: 005_create_user_invitations_and_auth_tables
Create Date: 2025-11-08 00:00:00.000000

This migration:
1. Creates the file_uploads table for tracking uploaded files
2. Supports complete ingestion lifecycle management
3. Includes security levels, approval workflow, and processing tracking
4. Provides performance monitoring and data retention policies
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '007'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create file_uploads table with comprehensive lifecycle tracking."""
    
    op.create_table(
        'file_uploads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        
        # Core identifiers
        sa.Column('upload_token', sa.String(length=255), nullable=False, unique=True),
        
        # File information
        sa.Column('file_name', sa.String(length=500), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=False),
        sa.Column('file_hash', sa.String(length=255), nullable=False),
        
        # User tracking
        sa.Column('uploaded_by_id', sa.Integer(), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('approval_reason', sa.Text(), nullable=True),
        
        # Department association and access control
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('is_department_only', sa.Boolean(), nullable=False, server_default=sa.false()),
        
        # Processing metadata
        sa.Column('file_purpose', sa.Text(), nullable=True),
        sa.Column('field_selection', sa.Text(), nullable=True),
        sa.Column('extraction_config', sa.Text(), nullable=True),
        
        # Security
        sa.Column('security_level', sa.String(length=50), nullable=False, server_default='internal'),
        
        # Processing tracking
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('is_processed', sa.Boolean(), nullable=False, server_default=sa.false()),
        
        # Processing results
        sa.Column('chunks_created', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('processing_error', sa.Text(), nullable=True),
        
        # Performance & monitoring
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        
        # Timestamps
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('processing_started_at', sa.DateTime(), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(), nullable=True),
        
        # Data retention
        sa.Column('retention_until', sa.DateTime(), nullable=True),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default=sa.false()),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='SET NULL'),
        
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes for common queries
    op.create_index(
        op.f('ix_file_upload_upload_token'),
        'file_uploads',
        ['upload_token'],
        unique=True
    )
    
    op.create_index(
        op.f('ix_file_upload_file_name'),
        'file_uploads',
        ['file_name'],
        unique=False
    )
    
    op.create_index(
        op.f('ix_file_upload_file_type'),
        'file_uploads',
        ['file_type'],
        unique=False
    )
    
    op.create_index(
        op.f('ix_file_upload_file_hash'),
        'file_uploads',
        ['file_hash'],
        unique=False
    )
    
    op.create_index(
        op.f('ix_file_upload_status'),
        'file_uploads',
        ['status'],
        unique=False
    )
    
    op.create_index(
        op.f('ix_file_upload_security_level'),
        'file_uploads',
        ['security_level'],
        unique=False
    )
    
    op.create_index(
        op.f('ix_file_upload_is_processed'),
        'file_uploads',
        ['is_processed'],
        unique=False
    )
    
    op.create_index(
        op.f('ix_file_upload_created_at'),
        'file_uploads',
        ['created_at'],
        unique=False
    )
    
    # Composite indexes for common queries
    op.create_index(
        op.f('idx_file_upload_status_created'),
        'file_uploads',
        ['status', 'created_at'],
        unique=False
    )
    
    op.create_index(
        op.f('idx_file_upload_user_status'),
        'file_uploads',
        ['uploaded_by_id', 'status'],
        unique=False
    )
    
    op.create_index(
        op.f('idx_file_upload_retention'),
        'file_uploads',
        ['retention_until', 'is_archived'],
        unique=False
    )
    
    # Department association indexes
    op.create_index(
        op.f('ix_file_upload_department_id'),
        'file_uploads',
        ['department_id'],
        unique=False
    )
    
    op.create_index(
        op.f('ix_file_upload_is_department_only'),
        'file_uploads',
        ['is_department_only'],
        unique=False
    )
    
    op.create_index(
        op.f('idx_file_upload_department_access'),
        'file_uploads',
        ['department_id', 'is_department_only'],
        unique=False
    )


def downgrade() -> None:
    """Drop file_uploads table."""
    
    op.drop_index(op.f('idx_file_upload_department_access'), table_name='file_uploads')
    op.drop_index(op.f('ix_file_upload_is_department_only'), table_name='file_uploads')
    op.drop_index(op.f('ix_file_upload_department_id'), table_name='file_uploads')
    op.drop_index(op.f('idx_file_upload_retention'), table_name='file_uploads')
    op.drop_index(op.f('idx_file_upload_user_status'), table_name='file_uploads')
    op.drop_index(op.f('idx_file_upload_status_created'), table_name='file_uploads')
    op.drop_index(op.f('ix_file_upload_created_at'), table_name='file_uploads')
    op.drop_index(op.f('ix_file_upload_is_processed'), table_name='file_uploads')
    op.drop_index(op.f('ix_file_upload_security_level'), table_name='file_uploads')
    op.drop_index(op.f('ix_file_upload_status'), table_name='file_uploads')
    op.drop_index(op.f('ix_file_upload_file_hash'), table_name='file_uploads')
    op.drop_index(op.f('ix_file_upload_file_type'), table_name='file_uploads')
    op.drop_index(op.f('ix_file_upload_file_name'), table_name='file_uploads')
    op.drop_index(op.f('ix_file_upload_upload_token'), table_name='file_uploads')
    
    op.drop_table('file_uploads')
