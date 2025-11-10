# Database Seeding Strategy

## Overview

RAG-Fortress uses an **idempotent seeding pattern** that ensures data safety and predictable behavior. Seeders never delete or replace existing data.

## Architecture Decision: Migrations First

### Why Separate?

1. **Separation of Concerns**
   - Migrations: Schema management (CREATE TABLE, ALTER COLUMN, etc.)
   - Seeders: Data initialization (INSERT initial records)

2. **Better Error Handling**
   - Migration failures are caught immediately
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
python migrate.py

# Step 2: Run seeders (data initialization)
python run_seeders.py
```

## Data Handling Strategy

### Principle: IDEMPOTENT + SAFE

Seeders follow these rules:

### 1. **No Deletion or Replacement**
- Existing data is NEVER deleted
- Existing data is NEVER updated or overwritten
- Seeders only INSERT new data

```python
# Seeders check existence before creating:
existing = await session.execute(
    select(Department).where(Department.code == "HR")
)
if existing.scalars().first():
    # Already exists - skip creation
    logger.debug(f"Department already exists")
    continue  # Don't insert
```

### 2. **Unique Constraint Enforcement**

For fields with unique constraints:

| Constraint | Existing Data | Attempt | Result |
|-----------|---------------|---------|--------|
| `UNIQUE` | Present | INSERT same | **ERROR** (Constraint Violation) |
| `UNIQUE` | Present | INSERT diff | **SUCCESS** (New record) |
| `UNIQUE` | Not present | INSERT | **SUCCESS** |

**Current Unique Fields:**

```
User:
  - username (unique)
  - email (unique)

Role:
  - name (unique)

Permission:
  - code (unique)

Department:
  - code (unique)

ApplicationSetting:
  - setting_name (unique)
```

### 3. **Behavior by Scenario**

#### Scenario A: Fresh Database (No Data)
```
Run: python run_seeders.py
Result: All seeders execute successfully
Output: "Created 4 roles, 10 permissions, 1 admin, 4 departments"
```

#### Scenario B: Partial Data (Some Seeders Already Run)
```
Database has: admin user, 4 roles, 4 departments
Run: python run_seeders.py
Result: 
  - Admin seeder: "Admin account already exists" (skipped)
  - Roles seeder: "All roles already exist" (skipped)
  - Departments seeder: "All departments already exist" (skipped)
```

#### Scenario C: Custom Data Added to Unique Field
```
Database has: User with username "admin" (created manually)
Run: python run_seeders.py with username="admin"
Result: 
  - Admin seeder: "Admin account already exists" (skipped)
  - No conflict, no error
```

#### Scenario D: CONFLICT - Unique Constraint Violation
```
Database has: Department with code "HR"
Run: Seeder tries to INSERT another code "HR"
Result:
  - ERROR: "UNIQUE constraint violation on departments.code"
  - Rollback triggered
  - Seeder fails with exception
```

## Migration Requirements Check

All seeders now validate that required tables exist BEFORE attempting to seed:

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

### Error Message Example

If tables don't exist:
```
ERROR | Failed to seed departments: Required table(s) missing: ['departments']. 
       Please run migrations first: python migrate.py
```

## Seeder Configuration

### Base Seeder Properties

```python
class BaseSeed(ABC):
    name: str                    # Seeder identifier
    description: str             # Human-readable description
    required_tables: list        # Tables that must exist (ENFORCED)
```

### Existing Seeders

| Seeder | Required Tables | Creates | Unique Checks |
|--------|-----------------|---------|---------------|
| `admin` | users, roles | 1 admin user | username, email |
| `roles_permissions` | roles, permissions | 4 roles, 10 permissions | name, code |
| `departments` | departments | 4 departments | code |

### Adding New Seeders

```python
from app.seeders.base import BaseSeed

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

## Error Handling

### Table Validation Errors
```
ERROR: Required table(s) missing: ['departments']. Please run migrations first: python migrate.py
```
**Action**: Run `python migrate.py` before running seeders

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

## Data Flow Diagram

```
┌─────────────────┐
│  Fresh Start    │
└────────┬────────┘
         │
         ├─→ python migrate.py
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

## FAQ

### Q: Can I run seeders multiple times?
**A**: Yes! Seeders are idempotent. Running them multiple times is safe. Already-seeded data will be skipped.

### Q: What if I want different seed data?
**A**: Modify the seeder files before running. Seeders only check for existing data, not content.

### Q: What if a unique constraint exists on my custom data?
**A**: Seeders will fail with a clear error. Either modify seeder data or check for manual data creation.

### Q: Can seeders modify existing data?
**A**: No. Seeders only INSERT. They never UPDATE or DELETE.

### Q: What's the performance impact?
**A**: 
- Migrations: One-time, typically <1 second
- Seeders: Depends on data volume, typically <1 second for default seeds

### Q: Should I run migrations and seeders in production?
**A**:
- **Migrations**: YES (via deployment pipeline)
- **Seeders**: DEPENDS on use case
  - If you want default data: YES
  - If data is already present: NO (skip, they won't harm anything)

## System Architecture Benefits

✅ **Clear Separation** - Each tool has single responsibility
✅ **Safe** - No data deletion or replacement
✅ **Idempotent** - Safe to run multiple times
✅ **Debuggable** - Clear error messages indicate what's wrong
✅ **Maintainable** - Easy to add new seeders following pattern
✅ **Production-Ready** - Follows database best practices
