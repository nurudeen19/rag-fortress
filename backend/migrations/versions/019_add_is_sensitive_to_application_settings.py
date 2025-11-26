"""add_is_sensitive_to_application_settings

Revision ID: 019
Revises: 018
Create Date: 2025-11-26 15:42:58.630063

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '019'
down_revision: Union[str, None] = '018'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Add is_sensitive column for tracking encrypted values
    op.add_column('application_settings',
                  sa.Column('is_sensitive', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    # Remove is_sensitive column
    op.drop_column('application_settings', 'is_sensitive')
