# Database Migrations - Quick Reference

## Common Commands

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

## Current Migrations

### Migration 001: Application Settings
- **Status**: ✓ Ready
- **Creates**: `application_settings` table
- **Purpose**: Store app configuration in database

### Migration 002: User Management
- **Status**: ✓ Ready
- **Creates**: 
  - `users` table
  - `roles` table (with defaults: admin, user, viewer)
  - `permissions` table (with 10 default permissions)
  - `user_roles` association table
  - `role_permissions` association table
- **Purpose**: User authentication, roles, and permissions

## Database Schema Overview

### application_settings
```
id (PK) | key (unique) | value | data_type | description | is_mutable | category | created_at | updated_at
```

### users
```
id (PK) | username (unique) | email (unique) | password_hash | full_name | bio | is_active | is_verified | created_at | updated_at
```

### roles
```
id (PK) | name (unique) | description | is_system | created_at | updated_at
```

### permissions
```
id (PK) | code (unique) | description | resource | action | created_at | updated_at
```

### user_roles (association)
```
user_id (FK, PK) | role_id (FK, PK)
```

### role_permissions (association)
```
role_id (FK, PK) | permission_id (FK, PK)
```

## Default Roles
- `admin` - Full access
- `user` - Regular user access
- `viewer` - Read-only access

## Default Permissions
- `user:create`, `user:read`, `user:update`, `user:delete`
- `document:create`, `document:read`, `document:update`, `document:delete`
- `settings:read`, `settings:update`

## Next Steps

1. **Run migrations**: `python migrate.py upgrade head`
2. **Verify tables**: Connect to database and check tables exist
3. **Create API endpoints**: Add FastAPI routes for user management
4. **Implement authentication**: Add JWT/session auth middleware

## Database Configuration

Set these environment variables to connect to different databases:

```bash
# PostgreSQL
export DATABASE_PROVIDER=postgresql
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=rag_fortress
export DB_PASSWORD=your_password
export DB_NAME=rag_fortress

# MySQL
export DATABASE_PROVIDER=mysql
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=rag_fortress
export DB_PASSWORD=your_password
export DB_NAME=rag_fortress

# SQLite (default)
export DATABASE_PROVIDER=sqlite
export SQLITE_PATH=./rag_fortress.db
```

## Files to Review

- `alembic.ini` - Alembic configuration
- `migrations/env.py` - Migration environment setup
- `app/models/application_setting.py` - ApplicationSetting model
- `app/models/user.py` - User/Role/Permission models
- `app/core/database.py` - Database connection management
