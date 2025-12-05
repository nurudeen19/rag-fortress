"""make_application_settings_value_nullable

Revision ID: 018
Revises: 017
Create Date: 2025-11-26 15:31:51.653109

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '018'
down_revision: Union[str, None] = '017'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Make value column nullable - users will provide values via UI
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('application_settings', schema=None) as batch_op:
        batch_op.alter_column('value',
                              existing_type=sa.Text(),
                              nullable=True)


def downgrade() -> None:
    # Revert to non-nullable (fill nulls with empty string first)
    op.execute("UPDATE application_settings SET value = '' WHERE value IS NULL")
    
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('application_settings', schema=None) as batch_op:
        batch_op.alter_column('value',
                              existing_type=sa.Text(),
                              nullable=False)
