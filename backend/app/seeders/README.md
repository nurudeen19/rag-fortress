# Database Seeders

Directory for database seeder modules. Each seeder handles one specific seeding operation.

## Usage

**Quick Start:**
```bash
# Run all seeders (via setup script)
python setup.py --all

# Or run seeders directly
python run_seeders.py --all
```

**Selective Seeding:**
```bash
# Run only specific seeders
python run_seeders.py --only-seeder admin,roles_permissions

# Run all except specified seeders
python run_seeders.py --skip-seeder departments,conversations

# List available seeders
python run_seeders.py --help
```

**Via setup.py:**
```bash
# Full setup: migrations + all seeders
python setup.py --all

# Run only specific seeders
python setup.py --only-seeder admin,roles_permissions

# Run all except specified
python setup.py --skip-seeder departments

# View available seeders
python setup.py --list-seeders
```

## Available Seeders

- **admin**: Creates admin user account from environment variables (`ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`)
- **roles_permissions**: Creates system roles (admin, manager, user, viewer) and default permissions
- **departments**: Creates sample department records
- **application_settings**: Creates application-level settings and configurations
- **jobs**: Creates sample background job records
- **knowledge_base**: Creates sample knowledge base entries
- **conversations**: Creates sample conversation threads
- **activity_logs**: Creates sample activity log entries

## Creating New Seeders

1. Create a new file in this directory (e.g., `files.py`)
2. Extend `BaseSeed` and implement the `run()` method
3. Add to `SEEDERS` dict in `__init__.py`

Example:

```python
# seeders/files.py
from app.seeders.base import BaseSeed

class FilesSeeder(BaseSeed):
    name = "files"
    description = "Creates default file structure"
    
    async def run(self, session, **kwargs) -> dict:
        # Your seeding logic
        return {"success": True, "message": "Files seeded"}
```

Then in `__init__.py`:

```python
from app.seeders.files import FilesSeeder

SEEDERS = {
    "admin": AdminSeeder,
    "roles_permissions": RolesPermissionsSeeder,
    "files": FilesSeeder,  # Add here
}
```

## Important Notes

- **Idempotent by Design**: Seeders are designed to be safe to run multiple times. Existing records are skipped to prevent duplicates.
- **No Default Behavior**: Seeder commands require explicit options (`--all`, `--only-seeder`, or `--skip-seeder`). Running without options shows help.
- **CLI Only**: Seeders are controlled via command-line flags. Environment variables are not supported.
