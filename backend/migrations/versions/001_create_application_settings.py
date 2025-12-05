"""create_application_settings_table

Revision ID: 001_create_application_settings
Revises: 
Create Date: 2025-11-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create application_settings table."""
    op.create_table(
        'application_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('data_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_mutable', sa.Boolean(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key', name=op.f('uq_application_settings_key')),
    )
    
    # Create indexes
    op.create_index(
        op.f('ix_application_settings_key'),
        'application_settings',
        ['key'],
        unique=True
    )
    op.create_index(
        op.f('ix_application_settings_category'),
        'application_settings',
        ['category'],
        unique=False
    )


def downgrade() -> None:
    """Drop application_settings table."""
    op.drop_index(op.f('ix_application_settings_category'), table_name='application_settings')
    op.drop_index(op.f('ix_application_settings_key'), table_name='application_settings')
    op.drop_table('application_settings')
