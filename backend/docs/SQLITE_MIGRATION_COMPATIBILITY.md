# Migration Compatibility Guide

## Overview
This document outlines the work completed to ensure all database migrations are compatible with SQLite, MySQL, and PostgreSQL without modification.

## Testing

### Multi-Provider Test Suite
A comprehensive test script has been created at `backend/test_all_db_providers.py` that validates all providers:

```bash
cd backend
# Test all providers (SQLite, MySQL, PostgreSQL)
python test_all_db_providers.py

# Test specific providers only
python test_all_db_providers.py --providers sqlite mysql
```

**Test Results:**
- ✅ **SQLite**: All 19 migrations, schema verification, seeders pass
- ✅ **MySQL**: All 19 migrations, schema verification, seeders pass  
- ✅ **PostgreSQL**: All 19 migrations, schema verification, seeders pass

**Requirements:**
- PostgreSQL: Requires `psycopg2-binary` package (installed automatically)
- MySQL: Requires `pymysql` package (included in requirements.txt)
- SQLite: No additional requirements (built into Python)

### SQLite-Specific Test
For detailed SQLite testing with CRUD operations:
```bash
cd backend
python test_sqlite_migration.py --clean
```

This test validates:
- ✅ All migrations run successfully with SQLite
- ✅ Schema is correctly created
- ✅ Seeders execute without errors
- ✅ Permission override operations function properly

## Key Changes Made

### 1. Batch Mode for SQLite

**Problem:** SQLite doesn't support `ALTER TABLE` operations outside of table creation.

**Solution:** Enabled Alembic's batch mode in `migrations/env.py`:

```python
context.configure(
    connection=connection,
    target_metadata=target_metadata,
    render_as_batch=True,  # Enable batch mode for SQLite
    # ... other config
)
```

### 2. Fixed Migrations

The following migrations were updated for cross-database compatibility:

#### Migration 007 - departments table
- **Issue:** Direct `op.add_column()` and `op.create_foreign_key()` calls
- **Fix:** Wrapped in `batch_alter_table` context manager

#### Migration 008 - security_level conversion
- **Issue:** Direct `op.alter_column()` call
- **Fix:** Wrapped in `batch_alter_table` context manager

#### Migration 014 - invitations department
- **Issue:** Direct column additions and foreign key creation
- **Fix:** Wrapped all operations in `batch_alter_table` for both upgrade and downgrade

#### Migration 015 - notifications table
- **Issue:** MySQL-specific `ON UPDATE CURRENT_TIMESTAMP` syntax
- **Fix:** Changed to standard `CURRENT_TIMESTAMP` (application handles updates)

#### Migration 016 - conversations and messages
- **Issue:** MySQL-specific `ON UPDATE CURRENT_TIMESTAMP` syntax
- **Fix:** Changed to standard `CURRENT_TIMESTAMP`

#### Migration 017 - activity_logs table
- **Issue:** MySQL-specific `ON UPDATE CURRENT_TIMESTAMP` syntax
- **Fix:** Changed to standard `CURRENT_TIMESTAMP`

#### Migration 018 - application_settings nullable
- **Issue:** Direct `op.alter_column()` call
- **Fix:** Wrapped in `batch_alter_table` context manager

#### Migration dbc6269d79ba - permission overrides approval
- **Issue:** Database-specific server defaults (`server_default='0'`)
- **Fix:** Changed to SQLAlchemy expressions (`sa.false()`, `sa.true()`, `sa.text('1')`)

## Database-Agnostic Patterns

### ✅ DO: Use Batch Mode for ALTER Operations

```python
def upgrade() -> None:
    with op.batch_alter_table('table_name', schema=None) as batch_op:
        batch_op.add_column(sa.Column('new_col', sa.String(50)))
        batch_op.create_foreign_key('fk_name', 'other_table', ['col'], ['id'])
```

### ✅ DO: Use SQLAlchemy Expressions for Defaults

```python
# Good - works across all databases
sa.Column('is_active', sa.Boolean(), server_default=sa.false())
sa.Column('count', sa.Integer(), server_default=sa.text('0'))

# Bad - database-specific
sa.Column('is_active', sa.Boolean(), server_default='0')  # SQLite treats as string
```

### ✅ DO: Use Standard CURRENT_TIMESTAMP

```python
# Good - works across all databases
sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'))

# Bad - MySQL-specific
sa.Column('updated_at', sa.DateTime(), 
          server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
```

### ❌ DON'T: Use Direct ALTER Operations

```python
# Bad - fails on SQLite
def upgrade() -> None:
    op.add_column('users', sa.Column('new_col', sa.String(50)))
    op.create_foreign_key('fk_users_dept', 'users', 'departments', ['dept_id'], ['id'])

# Good - works on all databases
def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('new_col', sa.String(50)))
        batch_op.create_foreign_key('fk_users_dept', 'departments', ['dept_id'], ['id'])
```

## Testing Checklist

When creating a new migration:

1. ✅ Use `batch_alter_table` for any ALTER operations
2. ✅ Use SQLAlchemy expressions for server defaults
3. ✅ Avoid database-specific syntax (ON UPDATE, etc.)
4. ✅ Test with SQLite: `python test_sqlite_migration.py --clean`
5. ✅ Verify both upgrade and downgrade functions

## Common Pitfalls

### 1. Column Comments
SQLite doesn't support column comments, but Alembic ignores them gracefully:
```python
sa.Column('name', sa.String(100), comment='User name')  # OK - ignored in SQLite
```

### 2. Server Defaults with Text
Be careful with `sa.text()` - ensure the SQL is compatible across databases:
```python
# Works on all databases
server_default=sa.text('CURRENT_TIMESTAMP')
server_default=sa.text("'approved'")  # String literal

# Database-specific - avoid
server_default=sa.text('NOW()')  # PostgreSQL-specific
server_default=sa.text('GETDATE()')  # SQL Server-specific
```

### 3. Boolean Values
SQLite stores booleans as integers (0/1):
```python
# Use SQLAlchemy expressions
server_default=sa.false()  # Correctly handles 0/1
server_default=sa.true()

# Not raw values
server_default='0'  # May be interpreted as string
```

## Verification

After making migration changes, always run:

```bash
# Clean test
python test_sqlite_migration.py --clean

# Test with existing database
python test_sqlite_migration.py
```

Expected output:
```
✓ Migrations completed successfully
✓ Schema verification passed
✓ All seeders completed successfully
✓ Data verification passed
✓ All permission override operations completed successfully

ALL TESTS PASSED ✓
```

## Benefits

1. **Single Migration Codebase**: Same migrations work across SQLite, MySQL, and PostgreSQL
2. **Easier Development**: Developers can use SQLite locally without Docker
3. **Faster CI/CD**: Tests can run with SQLite instead of requiring database containers
4. **Production Flexibility**: Choose any supported database provider without migration changes

## Related Files

- `backend/migrations/env.py` - Batch mode configuration
- `backend/test_sqlite_migration.py` - Comprehensive test suite
- `backend/migrations/versions/*` - All migration files (now SQLite-compatible)

## Support

If you encounter SQLite compatibility issues:

1. Check if the operation requires batch mode
2. Verify server defaults use SQLAlchemy expressions
3. Run the test script to identify the exact issue
4. Review the patterns in this guide

For MySQL/PostgreSQL-specific features that don't have SQLite equivalents (e.g., stored procedures), consider using conditional logic based on the database provider in the migration.
