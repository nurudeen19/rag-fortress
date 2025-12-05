"""Create jobs table for tracking async jobs and background processing.

Revision ID: 011_create_jobs_table
Revises: 010_create_permission_overrides_table
Create Date: 2025-11-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create jobs table for tracking async jobs and background processing."""
    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column(
            'job_type',
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            'status',
            sa.String(length=20),
            nullable=False,
            server_default='pending',
        ),
        sa.Column(
            'reference_id',
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            'reference_type',
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            'payload',
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            'result',
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            'error',
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            'retry_count',
            sa.Integer(),
            nullable=False,
            server_default=sa.text('0'),
        ),
        sa.Column(
            'max_retries',
            sa.Integer(),
            nullable=False,
            server_default=sa.text('3'),
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for efficient querying
    op.create_index(
        'ix_jobs_job_type',
        'jobs',
        ['job_type'],
        unique=False,
    )
    op.create_index(
        'ix_jobs_status',
        'jobs',
        ['status'],
        unique=False,
    )
    op.create_index(
        'ix_jobs_reference_id',
        'jobs',
        ['reference_id'],
        unique=False,
    )
    op.create_index(
        'ix_jobs_reference_type',
        'jobs',
        ['reference_type'],
        unique=False,
    )
    
    # Composite indexes for common queries
    op.create_index(
        'ix_jobs_status_type',
        'jobs',
        ['status', 'job_type'],
        unique=False,
    )
    op.create_index(
        'ix_jobs_reference',
        'jobs',
        ['reference_type', 'reference_id'],
        unique=False,
    )


def downgrade() -> None:
    """Drop jobs table."""
    op.drop_index('ix_jobs_reference', table_name='jobs')
    op.drop_index('ix_jobs_status_type', table_name='jobs')
    op.drop_index('ix_jobs_reference_type', table_name='jobs')
    op.drop_index('ix_jobs_reference_id', table_name='jobs')
    op.drop_index('ix_jobs_status', table_name='jobs')
    op.drop_index('ix_jobs_job_type', table_name='jobs')
    
    op.drop_table('jobs')
