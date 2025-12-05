"""Add approval workflow to permission_overrides

Revision ID: dbc6269d79ba
Revises: 019
Create Date: 2025-12-04 18:44:13.534606

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'dbc6269d79ba'
down_revision: Union[str, None] = '019'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Add approval workflow columns to permission_overrides table
    
    # Add new columns for permission override approval workflow
    op.add_column('permission_overrides', sa.Column('status', sa.String(length=20), nullable=False, server_default=sa.text("'approved'")))
    op.add_column('permission_overrides', sa.Column('approver_id', sa.Integer(), nullable=True))
    op.add_column('permission_overrides', sa.Column('approval_notes', sa.Text(), nullable=True))
    op.add_column('permission_overrides', sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('permission_overrides', sa.Column('trigger_query', sa.Text(), nullable=True))
    op.add_column('permission_overrides', sa.Column('trigger_file_id', sa.Integer(), nullable=True))
    op.add_column('permission_overrides', sa.Column('auto_escalated', sa.Boolean(), nullable=False, server_default=sa.text("'0'")))
    op.add_column('permission_overrides', sa.Column('escalated_at', sa.DateTime(timezone=True), nullable=True))
    
    # Create indexes for efficient queries
    op.create_index(op.f('ix_permission_overrides_status'), 'permission_overrides', ['status'], unique=False)
    op.create_index('ix_permission_overrides_status_created', 'permission_overrides', ['status', 'created_at'], unique=False)
    op.create_index('ix_permission_overrides_user_status', 'permission_overrides', ['user_id', 'status'], unique=False)
    
    # Add foreign key for approver using batch mode for SQLite compatibility
    with op.batch_alter_table('permission_overrides', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_permission_overrides_approver', 'users', ['approver_id'], ['id'], ondelete='SET NULL')
    
    # Add clearance level columns to user_invitations (for invitation system)
    with op.batch_alter_table('user_invitations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('org_level_permission', sa.Integer(), nullable=False, server_default=sa.text("'1'")))
        batch_op.add_column(sa.Column('department_level_permission', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # Reverse permission override approval workflow changes
    
    # Drop foreign key constraint using batch mode
    with op.batch_alter_table('permission_overrides', schema=None) as batch_op:
        batch_op.drop_constraint('fk_permission_overrides_approver', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('ix_permission_overrides_user_status', table_name='permission_overrides')
    op.drop_index('ix_permission_overrides_status_created', table_name='permission_overrides')
    op.drop_index(op.f('ix_permission_overrides_status'), table_name='permission_overrides')
    
    # Drop columns from permission_overrides using batch mode
    with op.batch_alter_table('permission_overrides', schema=None) as batch_op:
        batch_op.drop_column('escalated_at')
        batch_op.drop_column('auto_escalated')
        batch_op.drop_column('trigger_file_id')
        batch_op.drop_column('trigger_query')
        batch_op.drop_column('decided_at')
        batch_op.drop_column('approval_notes')
        batch_op.drop_column('approver_id')
        batch_op.drop_column('status')
    
    # Drop invitation clearance columns using batch mode
    with op.batch_alter_table('user_invitations', schema=None) as batch_op:
        batch_op.drop_column('department_level_permission')
        batch_op.drop_column('org_level_permission')
    # ### end Alembic commands ###
