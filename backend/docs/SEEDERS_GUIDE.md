# Database Seeders Guide

Complete guide to database seeding strategy, configuration, and usage in RAG-Fortress.

## Overview

RAG-Fortress uses an **idempotent seeding pattern** that ensures data safety and predictable behavior. Seeders never delete or replace existing data, making them safe to run multiple times.

## Architecture Decision: Migrations First

### Why Separate Migrations and Seeders?

1. **Separation of Concerns**
   - Migrations: Schema management (CREATE TABLE, ALTER COLUMN, etc.)
   - Seeders: Data initialization (INSERT initial records)

2. **Better Error Handling**
   - Migration failures caught immediately
   - Seeder failures don't create orphaned schema changes

3. **Idempotency**
   - Seeders can be safely re-run without side effects
   - Migrations are one-time structural changes

4. **Production Safety**
   - Migrations reviewed and deployed separately
   - Seeders run as data initialization step

### Recommended Workflow

```bash
# Step 1: Run migrations (schema creation)
python migrate.py upgrade head

# Step 2: Run seeders (data initialization)
python run_seeders.py
```

## Idempotent Seeding Strategy

### Core Principles

Seeders follow these rules:

#### 1. No Deletion or Replacement
- Existing data is NEVER deleted
- Existing data is NEVER updated or overwritten
- Seeders only INSERT new data

```python
# Seeders check existence before creating
existing = await session.execute(
    select(Department).where(Department.code == "HR")
)
if existing.scalars().first():
    # Already exists - skip creation
    logger.debug(f"Department already exists")
    continue  # Don't insert
```

#### 2. Unique Constraint Enforcement

For fields with unique constraints:

| Constraint | Existing Data | Attempt | Result |
|-----------|---------------|---------|--------|
| `UNIQUE` | Present | INSERT same | **ERROR** (Constraint Violation) |
| `UNIQUE` | Present | INSERT diff | **SUCCESS** (New record) |
| `UNIQUE` | Not present | INSERT | **SUCCESS** |

**Current Unique Fields:**
- User: `username`, `email`
- Role: `name`
- Permission: `code`
- Department: `code`
- ApplicationSetting: `setting_name`

#### 3. Migration Requirements Check

All seeders validate required tables exist BEFORE attempting to seed:

```python
class DepartmentsSeeder(BaseSeed):
    required_tables = ["departments"]
    
    async def run(self, session: AsyncSession, **kwargs):
        # Check tables exist
        tables_exist, missing = await self.validate_tables_exist(session)
        if not tables_exist:
            return {
                "success": False,
                "message": f"Required tables missing: {missing}. "
                           "Run migrations first: python migrate.py"
            }
        # ... proceed with seeding
```

## Seeder Configuration

### Available Seeders

| Seeder | Purpose | Required Tables | Dependencies |
|--------|---------|----------------|--------------|
| `roles_permissions` | Creates roles and permissions | `roles`, `permissions` | None |
| `admin` | Creates admin user account | `users`, `roles` | roles_permissions |
| `departments` | Creates department records | `departments` | None |
| `jobs` | Creates initial job records | `jobs` | None |
| `knowledge_base` | Creates knowledge base records | `knowledge_base` | None |

### Configuration Methods

**CLI Flags Only** - Seeders are controlled exclusively via command-line arguments. Environment variables are no longer supported.

```bash
# Run all seeders (migration + full setup)
python setup.py --all

# Run only specified seeders
python setup.py --only-seeder admin,roles_permissions

# Run all except specified seeders
python setup.py --skip-seeder departments,jobs

# View available seeders
python setup.py --list-seeders

# Verify database setup is complete
python setup.py --verify

# Clear database for reset
python setup.py --clear-db
```

Or run seeders directly:

```bash
# Run all seeders
python run_seeders.py --all

# Run only specific seeders
python run_seeders.py --only-seeder admin,roles_permissions

# Skip specific seeders
python run_seeders.py --skip-seeder departments
```

## Common Commands

### Full Setup (migrations + all seeders)
```bash
python setup.py --all
```
Runs migrations, all seeders, and verification.

### List Seeders
```bash
python setup.py --list-seeders
```
Shows all available seeders.

**Output:**
```
Available seeders:
  1. admin
  2. roles_permissions
  3. departments
  4. application_settings
  5. jobs
  6. knowledge_base
  7. conversations
  8. activity_logs

Total: 8 seeders available
```

### Run Only Specific Seeders
```bash
python setup.py --only-seeder admin,roles_permissions
```
Runs only the specified seeders (useful for production setup).

### Skip Specific Seeders
```bash
python setup.py --skip-seeder departments,jobs
```
Runs all seeders except the specified ones.

### Verify Setup
```bash
python setup.py --verify
```
Checks if all required tables exist.

### Clear Database
```bash
python setup.py --clear-db
```
Drops all tables (requires confirmation).

## Configuration Examples

### Development: Run Everything
```bash
python setup.py --all
# Runs all seeders
```

### Production: Minimal Setup
```bash
python setup.py --only-seeder admin,roles_permissions
# Runs only admin and roles_permissions (critical seeders)
```

### Staging: Most Features Except Optional
```bash
python setup.py --skip-seeder knowledge_base
# Runs all except knowledge_base
```

### Custom Combination
```bash
python setup.py --only-seeder admin,roles_permissions,departments,jobs
# Runs only specified seeders
```

## Seeder Behavior by Scenario

### Scenario A: Fresh Database (No Data)
```bash
Run: python run_seeders.py
Result: All seeders execute successfully
Output: "Created 4 roles, 10 permissions, 1 admin, 4 departments"
```

### Scenario B: Partial Data (Some Seeders Already Run)
```
Database has: admin user, 4 roles, 4 departments
Run: python run_seeders.py
Result: 
  - Admin seeder: "Admin account already exists" (skipped)
  - Roles seeder: "All roles already exist" (skipped)
  - Departments seeder: "All departments already exist" (skipped)
```

### Scenario C: Custom Data Added
```
Database has: User with username "admin" (created manually)
Run: python run_seeders.py with username="admin"
Result: 
  - Admin seeder: "Admin account already exists" (skipped)
  - No conflict, no error
```

### Scenario D: CONFLICT - Unique Constraint Violation
```
Database has: Department with code "HR"
Run: Seeder tries to INSERT another code "HR"
Result:
  - ERROR: "UNIQUE constraint violation on departments.code"
  - Rollback triggered
  - Seeder fails with exception
```

## Dependency Handling

The setup script automatically handles seeder dependencies:

- **admin** requires **roles_permissions**
  - If you request `admin` without `roles_permissions`, both will run
  - If you try to skip `roles_permissions`, it will still run if `admin` is enabled

Example:
```bash
# This command...
python setup.py --only-seeder admin

# Will automatically run:
# 1. roles_permissions (auto-added dependency)
# 2. admin

# Output shows:
# [INFO] Adding 'roles_permissions' (required by 'admin')
```

## Adding New Seeders

To add a new seeder without modifying `setup.py`:

### 1. Create Seeder Class

```python
# app/seeders/my_seeder.py
from app.seeders.base import BaseSeed
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class MySeeder(BaseSeed):
    name = "my_seeder"
    description = "Description of what this seeder does"
    required_tables = ["table1", "table2"]  # Tables that MUST exist
    
    async def run(self, session: AsyncSession, **kwargs) -> dict:
        try:
            # Validation: Tables exist?
            tables_exist, missing = await self.validate_tables_exist(session)
            if not tables_exist:
                return {
                    "success": False,
                    "message": f"Required tables missing: {missing}. Run migrations first."
                }
            
            # Create data
            created = 0
            for item in MY_DATA:
                # Check if exists
                existing = await session.execute(
                    select(MyModel).where(MyModel.unique_field == item["unique_field"])
                )
                if existing.scalars().first():
                    continue  # Skip if exists
                
                # Create new
                new_item = MyModel(**item)
                session.add(new_item)
                created += 1
            
            if created > 0:
                await session.commit()
                return {"success": True, "message": f"Created {created} items"}
            
            return {"success": True, "message": "All items already exist"}
            
        except Exception as e:
            await session.rollback()
            return {"success": False, "message": str(e)}
```

### 2. Register in `__init__.py`

```python
# app/seeders/__init__.py
from .my_seeder import MySeeder

SEEDERS = {
    "admin": AdminSeeder,
    "roles_permissions": RolesPermissionsSeeder,
    "departments": DepartmentsSeeder,
    "jobs": JobsSeeder,
    "knowledge_base": KnowledgeBaseSeeder,
    "my_seeder": MySeeder,  # Add here
}
```

### 3. Use Immediately

```bash
# No setup.py changes needed!
python setup.py --only-seeder my_seeder
python setup.py --skip-seeder my_seeder
python run_seeders.py --only-seeder my_seeder
```

## Base Seeder API

### BaseSeed Properties

```python
class BaseSeed(ABC):
    name: str                    # Seeder identifier
    description: str             # Human-readable description
    required_tables: list        # Tables that must exist (ENFORCED)
    
    async def run(self, session: AsyncSession, **kwargs) -> dict:
        """
        Run the seeder.
        
        Returns:
            dict: {
                "success": bool,
                "message": str,
                "created": int (optional)
            }
        """
        pass
    
    async def validate_tables_exist(self, session: AsyncSession) -> tuple:
        """
        Check if required tables exist.
        
        Returns:
            tuple: (tables_exist: bool, missing_tables: list)
        """
        pass
```

## Error Handling

### Table Validation Errors
```
ERROR: Required table(s) missing: ['departments']. 
       Please run migrations first: python migrate.py
```
**Action**: Run `python migrate.py upgrade head` before running seeders

### Unique Constraint Violations
```
ERROR: UNIQUE constraint violation on users.username
```
**Action**: Modify seeder data OR check if data already exists

### Database Connection Errors
```
ERROR: Database health check failed
```
**Action**: Check database is running and connection string is valid

### Seeder Execution Errors
```
✗ Critical seeders failed: admin
```
**Action**: 
- Check database connectivity
- Verify admin credentials in `.env`
- Run `python setup.py --clear-db` to reset

## Data Flow Diagram

```
┌─────────────────┐
│  Fresh Start    │
└────────┬────────┘
         │
         ├─→ python migrate.py upgrade head
         │   ├─ Create schema
         │   ├─ Create tables
         │   └─ Create indexes
         │
         ├─→ python run_seeders.py
         │   ├─ Check DB connection
         │   ├─ For each seeder:
         │   │  ├─ Validate required tables exist
         │   │  ├─ Check if data already exists
         │   │  ├─ If not exist: INSERT
         │   │  └─ If exists: SKIP
         │   └─ Commit all inserts
         │
         └─→ Ready to use!
```

## Real-World Examples

### Example 1: Fresh Development Environment
```bash
# Start from scratch with everything
python setup.py --clear-db
python setup.py --all
# Result: All seeders run, full setup
```

### Example 2: Production Deployment
```bash
python setup.py --only-seeder admin,roles_permissions
# Result: Minimal setup with only critical seeders
```

### Example 3: Skip Heavy Data
```bash
# Development but without large datasets
python setup.py --skip-seeder knowledge_base,jobs
# Result: Runs roles_permissions, departments, admin
```

### Example 4: One-Time Override
```bash
# Normally skip departments (in .env), but run it once
python setup.py --only-seeder admin,roles_permissions,departments
# Result: Overrides .env configuration
```

### Example 5: View What Will Run
```bash
# Before actually running setup
python setup.py --list-seeders

# Output shows:
# - Which seeders will run (✓ or ✗)
# - Current configuration (env vars or default)
# - Dependencies information
```

## Best Practices

### 1. Always Run Migrations First
```bash
# Good
python migrate.py upgrade head
python run_seeders.py

# Bad
python run_seeders.py  # May fail if tables don't exist
```

### 2. Check Existing Data
```python
# Good - check before insert
existing = await session.execute(
    select(Model).where(Model.unique_field == value)
)
if not existing.scalars().first():
    session.add(Model(...))

# Bad - assume data doesn't exist
session.add(Model(...))  # May violate unique constraint
```

### 3. Use Descriptive Messages
```python
# Good
return {"success": True, "message": "Created 4 departments"}

# Bad
return {"success": True, "message": "Done"}
```

### 4. Handle Errors Gracefully
```python
try:
    # ... seeding logic
    await session.commit()
    return {"success": True, "message": "..."}
except Exception as e:
    await session.rollback()
    return {"success": False, "message": str(e)}
```

### 5. Validate Table Existence
```python
# Always check required tables exist
tables_exist, missing = await self.validate_tables_exist(session)
if not tables_exist:
    return {
        "success": False,
        "message": f"Required tables missing: {missing}"
    }
```

## Troubleshooting

### Issue: "Critical seeders failed"
Error: `✗ Critical seeders failed: admin`

**Causes:**
- Admin already exists
- Database connectivity issues
- Invalid admin credentials in `.env`

**Solutions:**
```bash
# Clear everything and start fresh
python setup.py --clear-db
python setup.py

# Or skip admin if you don't need to recreate it
python setup.py --skip-seeder admin
```

### Issue: "Unknown seeders"
Error: `✗ Unknown seeders: my_seeder`

**Causes:**
- Seeder not registered in `SEEDERS` dict
- Typo in seeder name

**Solutions:**
```bash
# Check what's available
python setup.py --list-seeders

# Verify registration in app/seeders/__init__.py
```

### Issue: "Admin account already exists"
Message: `! admin: Admin account already exists`

This isn't an error - seeder detected existing data and skipped.

**Options:**
```bash
# Start fresh
python setup.py --clear-db
python setup.py

# Skip admin if you only need other seeders
python setup.py --skip-seeder admin
```

## Performance Characteristics

| Operation | Typical Time |
|-----------|-------------|
| Migrations | < 1 second |
| Seeders (default) | < 1 second |
| Full setup | < 5 seconds |

## System Architecture Benefits

✅ **Clear Separation** - Each tool has single responsibility
✅ **Safe** - No data deletion or replacement
✅ **Idempotent** - Safe to run multiple times
✅ **Debuggable** - Clear error messages indicate what's wrong
✅ **Maintainable** - Easy to add new seeders following pattern
✅ **Production-Ready** - Follows database best practices
✅ **Flexible Configuration** - Environment and CLI control
✅ **Future-Proof** - New seeders work automatically

## File Structure

```
app/seeders/
├── __init__.py                # Seeder registry
├── base.py                    # BaseSeed abstract class
├── admin_seeder.py            # Admin user seeder
├── roles_permissions_seeder.py # Roles & permissions seeder
├── departments_seeder.py      # Departments seeder
├── jobs_seeder.py             # Jobs seeder
└── knowledge_base_seeder.py   # Knowledge base seeder

backend/
├── setup.py                   # Main setup script with CLI
├── run_seeders.py             # Direct seeder execution
└── .env                       # Configuration file
```

## FAQ

### Q: Can I run seeders multiple times?
**A**: Yes! Seeders are idempotent. Already-seeded data will be skipped.

### Q: What if I want different seed data?
**A**: Modify the seeder files before running. Seeders only check for existing data, not content.

### Q: Can seeders modify existing data?
**A**: No. Seeders only INSERT. They never UPDATE or DELETE.

### Q: Should I run migrations and seeders in production?
**A**:
- **Migrations**: YES (via deployment pipeline)
- **Seeders**: DEPENDS on use case
  - If you want default data: YES
  - If data is already present: NO (safe to skip)

### Q: What's the performance impact?
**A**: 
- Migrations: One-time, typically < 1 second
- Seeders: Depends on data volume, typically < 1 second for defaults

---

**Status:** ✅ Production Ready
