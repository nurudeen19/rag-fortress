# Database Seeders

Directory for database seeder modules. Each seeder handles one specific seeding operation.

## Usage

Run all seeders:
```bash
python run_seeders.py
```

Run specific seeders:
```bash
python run_seeders.py admin
python run_seeders.py app
python run_seeders.py admin app
```

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
    "app": AppSeeder,
    "files": FilesSeeder,  # Add here
}
```

## Available Seeders

- **admin**: Creates default admin account from .env credentials
- **app**: Creates system roles (admin, user, viewer, moderator)
