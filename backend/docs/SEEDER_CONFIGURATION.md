# Seeder Configuration Guide

## Overview

The setup process now supports **flexible seeder configuration** through environment variables and CLI flags, allowing users to explicitly choose which seeders to run without any assumptions or environment detection logic.

**Key principle:** Empty configuration = Run all seeders (sensible default)

## Quick Start

### Run All Seeders (Default)
```bash
# No env vars set, no flags = run all 5 seeders
python setup.py
```

### Run Only Specific Seeders
```bash
# Option 1: Via environment variable
ENABLED_SEEDERS=admin,roles_permissions python setup.py

# Option 2: Via CLI flag (overrides env var)
python setup.py --only-seeder admin,roles_permissions
```

### Run All Except Specific Seeders
```bash
# Option 1: Via environment variable
DISABLED_SEEDERS=departments,jobs python setup.py

# Option 2: Via CLI flag (overrides env var)
python setup.py --skip-seeder departments,jobs
```

### View Current Configuration
```bash
python setup.py --list-seeders
```

## Configuration Methods

### Method 1: Environment Variables (Persistent)

Edit `.env` to set permanent defaults:

```env
# Option A: Run only these seeders
ENABLED_SEEDERS=admin,roles_permissions

# Option B: Run all except these (only if ENABLED_SEEDERS is empty)
DISABLED_SEEDERS=departments,jobs

# Option C: Leave both empty to run all
ENABLED_SEEDERS=
DISABLED_SEEDERS=
```

### Method 2: CLI Flags (Runtime Override)

```bash
# Run only specified seeders
python setup.py --only-seeder admin,roles_permissions,jobs

# Run all except specified seeders
python setup.py --skip-seeder departments

# View what will run
python setup.py --list-seeders
```

### Method 3: Priority Order

1. **CLI flags** (highest priority - always overrides everything)
   - `--only-seeder` or `--skip-seeder`
2. **Environment variables**
   - `ENABLED_SEEDERS` (if set, takes priority over DISABLED_SEEDERS)
   - `DISABLED_SEEDERS` (used if ENABLED_SEEDERS is empty)
3. **Default** (lowest priority)
   - If nothing is set, runs all available seeders

## Configuration Examples

### Development: Run Everything
```env
# .env - leave both empty (default)
ENABLED_SEEDERS=
DISABLED_SEEDERS=
```
```bash
python setup.py
# Runs all 5 seeders
```

### Production: Minimal Setup
```env
# .env - only critical seeders
ENABLED_SEEDERS=admin,roles_permissions
DISABLED_SEEDERS=
```
```bash
python setup.py
# Runs only admin and roles_permissions
```

### Staging: Most Features Except Optional
```env
# .env - skip only heavy/optional seeders
ENABLED_SEEDERS=
DISABLED_SEEDERS=knowledge_base
```
```bash
python setup.py
# Runs: roles_permissions, departments, admin, jobs (skips knowledge_base)
```

### Custom at Runtime
```bash
# Use CLI to override .env temporarily
ENABLED_SEEDERS= python setup.py --only-seeder admin,roles_permissions,departments
# Runs: admin, roles_permissions, departments (ignores .env ENABLED_SEEDERS)
```

## All CLI Commands

```bash
# Full setup with environment defaults
python setup.py

# Verify setup is complete
python setup.py --verify

# Reset database
python setup.py --clear-db

# Show configuration and available seeders
python setup.py --list-seeders

# Run only specified seeders (overrides env vars)
python setup.py --only-seeder admin,roles_permissions

# Run all except specified (overrides env vars)
python setup.py --skip-seeder departments,jobs
```

## Available Seeders

| Name | Purpose | Required | Dependencies |
|------|---------|----------|--------------|
| `roles_permissions` | Creates roles and permissions | Often | None |
| `admin` | Creates admin user account | Often | roles_permissions |
| `departments` | Creates department records | Optional | None |
| `jobs` | Creates initial job records | Optional | None |
| `knowledge_base` | Creates knowledge base records | Optional | None |

## Seeder Dependencies

The setup script automatically handles dependencies:

- **admin** requires **roles_permissions**
  - If you request `admin` without `roles_permissions`, both will run
  - If you try to skip `roles_permissions`, it will still run if `admin` is enabled

- Other seeders have no hard dependencies and can be run independently

Example:
```bash
# This works even though roles_permissions isn't explicitly listed
python setup.py --only-seeder admin
# Actually runs: roles_permissions, admin (auto-included)
```

## Adding New Seeders

To add a new seeder without modifying `setup.py` or these docs:

1. **Create seeder class** in `backend/app/seeders/`

2. **Register in `backend/app/seeders/__init__.py`**:
   ```python
   from .my_new_seeder import MyNewSeeder
   
   SEEDERS = {
       # ... existing seeders ...
       "my_seeder": MyNewSeeder,  # Add here
   }
   ```

3. **Use immediately** - no other changes needed:
   ```bash
   python setup.py --only-seeder my_seeder
   python setup.py --skip-seeder my_seeder
   ENABLED_SEEDERS=my_seeder python setup.py
   ```

The new seeder automatically works with all commands, environment variables, and CLI flags.

## Troubleshooting

### Issue: "Critical seeders failed"
Error: `✗ Critical seeders failed: admin`

**Causes:**
- Admin already created (database has data)
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

# Verify registration in backend/app/seeders/__init__.py
```

### Issue: "Admin account already exists"
Message: `! admin: Admin account already exists`

This isn't necessarily an error - it means the seeder ran but data was already there.

**Options:**
```bash
# Start fresh
python setup.py --clear-db
python setup.py

# Skip admin if you only need other seeders
python setup.py --skip-seeder admin
```

## Real-World Examples

### Example 1: Fresh Development Environment
```bash
# Start from scratch with everything
python setup.py --clear-db
python setup.py
# Result: All 5 seeders run, full setup
```

### Example 2: Production Deployment
```env
# .env
ENABLED_SEEDERS=admin,roles_permissions
```
```bash
python setup.py
# Result: Minimal setup with only critical seeders
```

### Example 3: Skip Heavy Data
```bash
# Development but without large datasets
python setup.py --skip-seeder knowledge_base,jobs
# Result: Runs roles_permissions, departments, admin (skips knowledge_base and jobs)
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

## Configuration File Location

All configuration is in `backend/.env`:

```bash
# View current setup
python setup.py --list-seeders

# Edit defaults
# nano .env
# or
# code .env

# Key variables:
ENABLED_SEEDERS=         # Leave empty or set to list
DISABLED_SEEDERS=        # Leave empty or set to list
```

## Design Philosophy

This approach is based on these principles:

✓ **Explicit is better than implicit** - No magic environment detection
✓ **Empty = sensible default** - Run all seeders by default
✓ **User-controlled** - User decides what to run/skip
✓ **No assumptions** - Works same way everywhere
✓ **Future-proof** - New seeders work automatically
✓ **Clear configuration** - Simple, understandable rules

---

See `SEEDER_CONFIGURATION_QUICK_REF.md` for quick command reference.

### Seeder List

Available seeders:

| Seeder | Purpose | Required | Dependencies |
|--------|---------|----------|--------------|
| `roles_permissions` | Creates roles and permissions | Critical | None |
| `admin` | Creates admin user account | Critical | roles_permissions |
| `departments` | Creates department records | Optional | None |
| `jobs` | Creates initial job records | Optional | None |
| `knowledge_base` | Creates knowledge base records | Optional | None |

## CLI Commands

### Full Setup (with environment defaults)
```bash
python setup.py
```
Runs migrations, seeders (based on ENVIRONMENT), and verification.

### List Seeders
```bash
python setup.py --list-seeders
```
Shows available seeders and which ones will run based on current configuration.

Output:
```
Available seeders:
  ✓ admin
  ✓ roles_permissions
  ✗ departments
  ✗ knowledge_base
  ✗ jobs

Current environment: production
Seeders to run: admin, roles_permissions

Seeder dependencies:
  • roles_permissions: No dependencies
  • departments: Optional
  • admin: Requires roles_permissions
  • jobs: Optional
  • knowledge_base: Optional
```

### Run Only Specific Seeders
```bash
python setup.py --only-seeder admin,roles_permissions
```
Ignores environment defaults and runs only specified seeders.

### Skip Specific Seeders
```bash
python setup.py --skip-seeder departments
```
Runs all default seeders except the specified ones.

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

## Dependency Handling

The setup script automatically handles seeder dependencies:

- If you request `admin` without `roles_permissions`, the script automatically includes `roles_permissions` first
- Dependencies are respected regardless of CLI flag order
- Dependencies are logged so users know what's happening

Example:
```bash
# This command...
python setup.py --only-seeder admin

# Will automatically run:
# 1. roles_permissions (auto-added dependency)
# 2. admin

# Output shows:
# [INFO]   [INFO] Adding 'roles_permissions' (required by 'admin')
```

## Adding New Seeders

To add a new seeder without modifying `setup.py`:

1. **Create seeder class** in `backend/app/seeders/`
2. **Register in `__init__.py`** by updating the `SEEDERS` dictionary:
   ```python
   from .my_new_seeder import MyNewSeeder
   
   SEEDERS = {
       "admin": AdminSeeder,
       "roles_permissions": RolesPermissionsSeeder,
       "departments": DepartmentsSeeder,
       "jobs": JobsSeeder,
       "knowledge_base": KnowledgeBaseSeeder,
       "my_new_seeder": MyNewSeeder,  # Add here
   }
   ```
3. **Update `.env`** (optional) to include in defaults:
   ```env
   ENABLED_SEEDERS_DEV=roles_permissions,departments,admin,jobs,knowledge_base,my_new_seeder
   ENABLED_SEEDERS_PROD=admin,roles_permissions
   ```

The seeder is now available for use without any changes to `setup.py`.

## Environment-Based Strategy

### Development
- Purpose: Complete setup for local development
- Default seeders: All (roles_permissions, departments, admin, jobs, knowledge_base)
- Use case: Fresh database setup during development

```bash
# In development
python setup.py  # Uses ENABLED_SEEDERS_DEV
```

### Production
- Purpose: Minimal but functional setup
- Default seeders: Critical only (admin, roles_permissions)
- Use case: Production deployments with minimal data initialization

```bash
# In production
ENVIRONMENT=production python setup.py  # Uses ENABLED_SEEDERS_PROD
```

### Hybrid (Custom)
- Use CLI flags to override defaults at runtime

```bash
# Production instance but need additional seeders
ENVIRONMENT=production python setup.py --only-seeder admin,roles_permissions,jobs
```

## Troubleshooting

### "Critical seeders failed"
This means `admin` or `roles_permissions` failed to run. Check:
1. Database connectivity
2. Admin credentials in `.env` (ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD)
3. Run `python setup.py --clear-db` to reset and try again

### "Unknown seeders"
The seeder name doesn't exist in `SEEDERS` dict. Check:
1. Seeder is registered in `backend/app/seeders/__init__.py`
2. Seeder class name is correct in the dict

### "Admin account already exists"
The seeder ran before and admin already created. Options:
1. Run `python setup.py --clear-db` to reset
2. Run `python setup.py --skip-seeder admin` to skip admin and run others

## Examples

### Example 1: Development Fresh Setup
```bash
# Start fresh in development
python setup.py --clear-db
python setup.py
# Result: Full setup with all seeders
```

### Example 2: Production with Only Admin
```bash
# Minimal production setup
ENVIRONMENT=production python setup.py
# Uses ENABLED_SEEDERS_PROD (admin, roles_permissions)
# Result: Only critical seeders run
```

### Example 3: Add Optional Seeders to Production
```bash
# Production setup + departments
ENVIRONMENT=production python setup.py --only-seeder admin,roles_permissions,departments
# Result: Runs all three specified seeders
```

### Example 4: Development Without Departments
```bash
# Full dev setup except departments
python setup.py --skip-seeder departments
# Result: Runs all except departments
```

## Configuration File Location

All configuration is in `.env`:

```bash
# View your current setup
python setup.py --list-seeders

# To change defaults, edit .env:
# ENVIRONMENT=development
# ENABLED_SEEDERS_DEV=roles_permissions,departments,admin,jobs,knowledge_base
# ENABLED_SEEDERS_PROD=admin,roles_permissions
```

## Future-Proof Design

This approach is designed to support new seeders without modifying `setup.py`:

- New seeders only require registration in `SEEDERS` dict
- Environment configuration happens in `.env`, not code
- CLI flags work automatically with new seeders
- No setup.py modifications needed

Example: Adding a "users" seeder:
```python
# Only change: register in __init__.py
SEEDERS = {
    # ... existing seeders ...
    "users": UsersSeeder,  # New seeder automatically available
}
```

Then use it:
```bash
python setup.py --only-seeder admin,roles_permissions,users
```

No `setup.py` changes required!
