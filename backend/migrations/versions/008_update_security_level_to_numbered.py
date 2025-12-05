"""update_security_level_to_numbered

Revision ID: 008_update_security_level_to_numbered
Revises: 007_create_departments_table
Create Date: 2025-11-08 00:00:00.000000

This migration:
1. Changes security_level column from STRING enum to INTEGER enum
2. Maps old string values to new numeric tier values:
   - "public" → 1
   - "internal" → 2
   - "confidential" → 3
   - "restricted" → 4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '006'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Migrate security_level from string to numbered tier structure."""
    
    # Step 1: Migrate existing data from string to integer values
    op.execute("""
        UPDATE file_uploads
        SET security_level = CASE
            WHEN security_level = 'public' THEN '1'
            WHEN security_level = 'internal' THEN '2'
            WHEN security_level = 'confidential' THEN '3'
            WHEN security_level = 'restricted' THEN '4'
            ELSE '2'
        END
    """)
    
    # Step 2: Drop the old index
    op.drop_index(op.f('ix_file_upload_security_level'), table_name='file_uploads')
    
    # Step 3: Alter the column to INTEGER type - handle differently per database
    # PostgreSQL requires explicit USING clause and default must be dropped first
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        # Drop old default first
        op.execute("""
            ALTER TABLE file_uploads 
            ALTER COLUMN security_level DROP DEFAULT
        """)
        # Change type with USING clause
        op.execute("""
            ALTER TABLE file_uploads 
            ALTER COLUMN security_level TYPE INTEGER 
            USING security_level::integer
        """)
        # Set new default
        op.execute("""
            ALTER TABLE file_uploads 
            ALTER COLUMN security_level SET DEFAULT 2
        """)
    else:
        # MySQL and SQLite can use batch mode
        with op.batch_alter_table('file_uploads', schema=None) as batch_op:
            batch_op.alter_column(
                'security_level',
                existing_type=sa.String(length=50),
                type_=sa.Integer(),
                existing_nullable=False,
                existing_server_default='internal',
                server_default=sa.text("'2'")
            )
    
    # Step 4: Recreate the index
    op.create_index(
        op.f('ix_file_upload_security_level'),
        'file_uploads',
        ['security_level'],
        unique=False
    )


def downgrade() -> None:
    """Revert security_level from numbered tier back to string enum."""
    
    # Step 1: Drop the numeric index
    op.drop_index(op.f('ix_file_upload_security_level'), table_name='file_uploads')
    
    # Step 2: Migrate data back from integer to string
    op.execute("""
        UPDATE file_uploads
        SET security_level = CASE
            WHEN security_level = 1 THEN 'public'
            WHEN security_level = 2 THEN 'internal'
            WHEN security_level = 3 THEN 'confidential'
            WHEN security_level = 4 THEN 'restricted'
            ELSE 'internal'
        END
    """)
    
    # Step 3: Alter the column back to STRING type - handle differently per database
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        # Drop numeric default first
        op.execute("""
            ALTER TABLE file_uploads 
            ALTER COLUMN security_level DROP DEFAULT
        """)
        # Change type with USING clause
        op.execute("""
            ALTER TABLE file_uploads 
            ALTER COLUMN security_level TYPE VARCHAR(50) 
            USING security_level::varchar
        """)
        # Set string default
        op.execute("""
            ALTER TABLE file_uploads 
            ALTER COLUMN security_level SET DEFAULT 'internal'
        """)
    else:
        # MySQL and SQLite can use batch mode
        with op.batch_alter_table('file_uploads', schema=None) as batch_op:
            batch_op.alter_column(
                'security_level',
                existing_type=sa.Integer(),
                type_=sa.String(length=50),
                existing_nullable=False,
                existing_server_default='2',
                server_default=sa.text("'internal'")
            )
    
    # Step 4: Recreate the index
    op.create_index(
        op.f('ix_file_upload_security_level'),
        'file_uploads',
        ['security_level'],
        unique=False
    )
