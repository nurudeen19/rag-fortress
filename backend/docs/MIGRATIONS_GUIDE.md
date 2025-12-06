# SQLAlchemy Migrations Setup Guide

## Overview

This project uses **SQLAlchemy** as the ORM and **Alembic** for database migrations. This guide covers the migration infrastructure, how to use it, and best practices.

## Directory Structure

```
backend/
├── alembic.ini                          # Alembic configuration file
├── migrate.py                           # CLI script for running migrations
├── migrations/                          # Alembic migrations directory
│   ├── __init__.py
│   ├── env.py                          # Alembic environment configuration
│   ├── script.py.mako                  # Migration template
│   └── versions/                       # Migration files
│       ├── 001_create_application_settings.py
│       └── 002_create_user_management.py
└── app/
    ├── models/                         # SQLAlchemy ORM models
    │   ├── __init__.py                # Model exports
    │   ├── base.py                    # Base model class with common fields
    │   ├── application_setting.py     # ApplicationSetting model
    │   └── user.py                    # User, Role, Permission models
    └── core/
        └── database.py                # Database connection management
```

## Initial Migrations

Two initial migrations have been created:

### 1. `001_create_application_settings.py`
Creates the `application_settings` table for storing application-level configuration in the database.

**Table: `application_settings`**
- `id`: Primary key
- `key`: Unique setting key (indexed)
- `value`: Setting value as text
- `data_type`: Type of the setting (string, integer, boolean, json)
- `description`: Human-readable description
- `is_mutable`: Whether the setting can be modified via API
- `category`: Category for grouping settings
- `created_at`, `updated_at`: Timestamps

### 2. `002_create_user_management.py`
Creates the complete user management system with roles and permissions.

**Tables created:**
- **`users`**: Main user table
  - Username, email (both unique and indexed)
  - Password hash
  - Full name, bio
  - `is_active`, `is_verified` flags
  - Indexes on username, email, is_active, created_at

- **`roles`**: Role definitions for RBAC
  - Role name (unique)
  - Description
  - `is_system` flag (indicates system-managed roles)
  - Pre-populated with: admin, user, viewer

- **`permissions`**: Fine-grained permission definitions
  - Code (unique, e.g., "document:create")
  - Resource and action
  - Description
  - Indexes on code, resource, and resource+action
  - Pre-populated with default permissions for users, documents, and settings

- **`user_roles`**: Many-to-many association (users ↔ roles)
  - Foreign keys to users and roles with CASCADE delete

- **`role_permissions`**: Many-to-many association (roles ↔ permissions)
  - Foreign keys to roles and permissions with CASCADE delete

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run All Pending Migrations
```bash
python migrate.py upgrade head
```

This will:
- Create the `application_settings` table
- Create all user management tables
- Insert default roles (admin, user, viewer)
- Insert default permissions

### 3. Check Migration Status
```bash
python migrate.py current
```

### 4. View Migration History
```bash
python migrate.py history
```

## CLI Commands

The `migrate.py` script provides the following commands:

### Apply migrations
```bash
python migrate.py upgrade head
```
Applies all pending migrations up to the latest version.

### Rollback migrations
```bash
python migrate.py downgrade -1
```
Rolls back the last applied migration.

### Check current migration
```bash
python migrate.py current
```
Shows the current migration version.

### View migration history
```bash
python migrate.py history
```
Shows the complete migration history.

### Create new migration
```bash
python migrate.py revision -m "your migration message"
```
Creates a new empty migration file that you can edit.

## Creating New Migrations

### Manual Migration (Recommended for complex changes)

1. **Create an empty migration file:**
```bash
python migrate.py revision -m "add_user_profile_table"
```

2. **Edit the generated file in `migrations/versions/`:**
```python
def upgrade() -> None:
    """Create user_profile table."""
    op.create_table(
        'user_profile',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

def downgrade() -> None:
    """Drop user_profile table."""
    op.drop_table('user_profile')
```

3. **Apply the migration:**
```bash
python migrate.py upgrade head
```

### Auto-generated Migration (For simple model changes)

If you modify a model and want Alembic to detect the changes:

1. **Update your model in `app/models/`**

2. **Generate migration from model changes:**
```bash
# This requires autogenerate to be enabled in env.py
# Currently, it's set to manual migration mode
```

**Note:** Auto-generation is not enabled by default in this project. This is intentional to avoid unexpected migrations. Always review and test migrations manually.

## Model Changes and Migrations

When you add a new model or modify an existing one:

1. **Add/modify the model in `app/models/`**
2. **Ensure it inherits from `Base`**
3. **Create a migration file**
4. **Test the migration thoroughly**
5. **Apply the migration**

### Example: Adding a New Model

```python
# In app/models/document.py
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class Document(Base):
    __tablename__ = "documents"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
```

Then create a migration:
```bash
python migrate.py revision -m "create_documents_table"
```

## Migration Best Practices

1. **Always review migrations before applying them**
   - Check the SQL that will be executed
   - Ensure all constraints and indexes are correct

2. **Test migrations on a dev database first**
   - Don't apply untested migrations to production

3. **Use descriptive migration names**
   - Good: `003_add_document_category_field`
   - Bad: `003_updates`

4. **One logical change per migration**
   - Don't mix creating tables with adding columns to existing tables if they're unrelated

5. **Always write both `upgrade()` and `downgrade()`**
   - Ensure rollbacks work correctly
   - Test rollbacks on dev database

6. **Handle data migrations carefully**
   - Use `op.execute()` for data changes
   - Consider the impact on existing data

7. **Use meaningful foreign key constraints**
   - Always set `ondelete='CASCADE'` or `ondelete='RESTRICT'` as appropriate
   - This prevents orphaned records

## Environment-Specific Configuration

The migration system respects the `DATABASE_PROVIDER` environment variable:

```bash
# SQLite (default for development)
export DATABASE_PROVIDER=sqlite

# PostgreSQL (recommended for production)
export DATABASE_PROVIDER=postgresql
export DB_HOST=localhost
export DB_USER=rag_fortress
export DB_PASSWORD=your_password
export DB_NAME=rag_fortress

# MySQL
export DATABASE_PROVIDER=mysql
export DB_HOST=localhost
export DB_USER=rag_fortress
export DB_PASSWORD=your_password
export DB_NAME=rag_fortress
```

## Database Models

### ApplicationSetting
Stores application configuration that can be modified at runtime.

```python
from app.models import ApplicationSetting

# Create a setting
setting = ApplicationSetting(
    key="max_document_size",
    value="100MB",
    data_type="string",
    category="documents",
    is_mutable=True,
)
```

### User
Represents a user in the system.

```python
from app.models import User

# Create a user
user = User(
    username="john_doe",
    email="john@example.com",
    password_hash="hashed_password_here",
    full_name="John Doe",
    is_active=True,
    is_verified=False,
)
```

### Role
Represents a role in the RBAC system. Pre-populated with: `admin`, `user`, `viewer`.

```python
from app.models import Role

# Assign role to user
admin_role = session.query(Role).filter(Role.name == "admin").first()
user.roles.append(admin_role)
```

### Permission
Represents a specific permission. Examples:
- `document:create` - Create documents
- `user:delete` - Delete users
- `settings:update` - Update settings

### Association Tables
- `user_roles`: Links users to roles
- `role_permissions`: Links roles to permissions

## Common Tasks

### Check if a user has permission
```python
# Through role membership
user.has_role("admin")

# Through permission assignment (custom implementation needed)
# Check if any role has a specific permission
```

### Add a new default permission
Create a migration and add to the `permissions` table:

```python
def upgrade() -> None:
    permissions_table = sa.table(
        'permissions',
        sa.column('code'),
        sa.column('resource'),
        sa.column('action'),
        # ... other columns
    )
    
    op.bulk_insert(
        permissions_table,
        [
            {
                'code': 'document:share',
                'resource': 'document',
                'action': 'share',
                # ... other fields
            }
        ]
    )
```

### Backup and Restore

**PostgreSQL:**
```bash
# Backup
pg_dump -U rag_fortress rag_fortress > backup.sql

# Restore
psql -U rag_fortress rag_fortress < backup.sql
```

**MySQL:**
```bash
# Backup
mysqldump -u rag_fortress -p rag_fortress > backup.sql

# Restore
mysql -u rag_fortress -p rag_fortress < backup.sql
```

**SQLite:**
```bash
# Backup
cp rag_fortress.db rag_fortress.db.backup
```

## Troubleshooting

### Migration fails with "Table already exists"
- The migration may have been partially applied
- Check the migration history: `python migrate.py history`
- Manually verify the database state

### Cannot connect to database
- Verify environment variables are set correctly
- Check database credentials
- Ensure database server is running

### Downgrade fails
- Ensure the downgrade function is correctly implemented
- Test downgrades on a dev database first
- Check for data integrity issues

## Quick Reference Commands

### Common Commands

```bash
# Apply all pending migrations
python migrate.py upgrade head

# Rollback last migration
python migrate.py downgrade -1

# Check current migration version
python migrate.py current

# View migration history
python migrate.py history

# Create new migration
python migrate.py revision -m "description"
```

### Current Migrations Status

| Migration | Tables Created | Purpose |
|-----------|---------------|---------|
| 001 | `application_settings` | Store app configuration in database |
| 002 | `users`, `roles`, `permissions`, associations | User authentication, RBAC |
| 003+ | Various tables | Additional features |

### Default Data

**Roles:** admin, user, viewer

**Permissions:**
- `user:create`, `user:read`, `user:update`, `user:delete`
- `document:create`, `document:read`, `document:update`, `document:delete`
- `settings:read`, `settings:update`

## SQLite Compatibility

All migrations are compatible with SQLite, MySQL, and PostgreSQL without modification.

### Batch Mode for SQLite

SQLite doesn't support `ALTER TABLE` operations outside of table creation. All migrations use Alembic's batch mode:

```python
# migrations/env.py
context.configure(
    connection=connection,
    target_metadata=target_metadata,
    render_as_batch=True,  # Enable batch mode for SQLite
    # ... other config
)
```

### Testing Multi-Provider Compatibility

A comprehensive test suite validates all providers:

```bash
cd backend

# Test all providers (SQLite, MySQL, PostgreSQL)
python test_all_db_providers.py

# Test specific providers only
python test_all_db_providers.py --providers sqlite mysql
```

**Test Results:**
- ✅ SQLite: All migrations, schema verification, seeders pass
- ✅ MySQL: All migrations, schema verification, seeders pass  
- ✅ PostgreSQL: All migrations, schema verification, seeders pass

**Requirements:**
- PostgreSQL: Requires `psycopg2-binary` package
- MySQL: Requires `pymysql` package
- SQLite: No additional requirements

### SQLite-Specific Testing

For detailed SQLite testing with CRUD operations:

```bash
cd backend
python test_sqlite_migration.py --clean
```

This validates:
- ✅ All migrations run successfully
- ✅ Schema is correctly created
- ✅ Seeders execute without errors
- ✅ CRUD operations function properly

## Database-Agnostic Migration Patterns

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

## Provider-Agnostic Migration Checklist

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

## Benefits of Multi-Provider Support

1. **Single Migration Codebase** - Same migrations work across SQLite, MySQL, and PostgreSQL
2. **Easier Development** - Developers can use SQLite locally without Docker
3. **Faster CI/CD** - Tests can run with SQLite instead of requiring database containers
4. **Production Flexibility** - Choose any supported database provider without migration changes

## References

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Database Settings Configuration](../app/config/database_settings.py)
