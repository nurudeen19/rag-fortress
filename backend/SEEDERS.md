# Seeders Implementation

## Structure

```
app/seeders/
├── __init__.py          # Registry of all seeders
├── base.py              # BaseSeed abstract class
├── admin.py             # AdminSeeder
├── app.py               # AppSeeder
└── README.md            # Guide for adding new seeders
```

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

The runner will warn about data removal before proceeding.

## Adding New Seeders

1. Create file in `app/seeders/` (e.g., `files.py`)
2. Extend `BaseSeed` and implement `async def run()`
3. Register in `app/seeders/__init__.py` in `SEEDERS` dict

Each seeder is responsible for one thing and is completely independent.
