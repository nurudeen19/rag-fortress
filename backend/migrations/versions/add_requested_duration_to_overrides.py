"""Add requested_duration_hours column to permission_overrides

Revision ID: 021_add_requested_duration
Revises: 020
Create Date: 2025-12-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '021'
down_revision: Union[str, None] = '020'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Add requested_duration_hours column to permission_overrides table."""
    # Add the missing column with a default value
    with op.batch_alter_table('permission_overrides', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'requested_duration_hours',
                sa.Integer(),
                nullable=False,
                server_default=sa.text("24")
            )
        )


def downgrade() -> None:
    """Remove requested_duration_hours column from permission_overrides table."""
    with op.batch_alter_table('permission_overrides', schema=None) as batch_op:
        batch_op.drop_column('requested_duration_hours')
