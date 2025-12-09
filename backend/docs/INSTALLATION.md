# Installation Guide

## Prerequisites

- Python 3.11 or higher
- `uv` package manager (modern, fast Python package manager)

## Quick Start

### 1. Install uv (if needed)

**Windows:**
```powershell
powershell -ExecutionPolicy BypassCurrentUser -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify: `uv --version`

### 2. Setup Backend

```bash
cd backend
uv sync
```

This will:
- Create a `.venv` virtual environment
- Install all production and development dependencies with pinned versions

### 3. Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your configuration:
- Database connection details
- LLM API keys (OPENAI_API_KEY, GOOGLE_API_KEY, etc.)
- Vector store settings
- Email configuration (optional but required to use invitation system)
- Other application settings

### 5. Initialize Database and Load Seeders

**Note:** If you plan to use **PostgreSQL** or **MySQL**, make sure the database server is installed and a database is created and reachable before running the setup. The connection details are taken from your database settings `DB_HOST`,`DB_PORT` etc. in `.env`. For **SQLite** no external database server is required — the database file will be created automatically when migrations run.

```bash
python setup.py
```

This single command will:
- Run all database migrations
- Load initial seed data (demo users, roles, permissions)
- Set up the database schema

**Optional:** To run migrations and seeders separately:
```bash
python migrate.py      # Run migrations only
python run_seeders.py  # Run seeders only
```

### Seeders (selective control)

- **Run all seeders (default):** `python setup.py` runs migrations then all seeders.
- **Run seeders only:** `python run_seeders.py` runs all seeders unless you pass specific names.
- **Run specific seeders (CLI):** pass seeder names to `run_seeders.py` or use `setup.py` flags.
	- Example: `python run_seeders.py admin` — runs only the `admin` seeder.
	- Example: `python run_seeders.py admin app` — runs `admin` and `app` (order follows seeding order).
- **Using `setup.py` for selective seeding:**
	- `python setup.py --only-seeder admin,roles_permissions` — run only those seeders.
	- `python setup.py --skip-seeder departments,jobs` — run all except those.
- **Environment variables to control seeders:**
	- `ENABLED_SEEDERS` — comma-separated list of seeders to run (highest priority).
	- `DISABLED_SEEDERS` — comma-separated list of seeders to skip (used if ENABLED_SEEDERS not set).
	- CLI flags (`--only-seeder`, `--skip-seeder`) override these environment variables.
- **Admin seeder configuration:** the admin seeder reads credentials from AppSettings / environment variables:
	- `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` (optional: `ADMIN_FIRSTNAME`, `ADMIN_LASTNAME`).
	- Set these in your `.env` before running seeders to control the created admin account.

Note: Seeders are implemented to be idempotent where possible. If a seeder detects existing records (unique constraints), it will skip or warn rather than duplicate data.

### 6. Start the Server

```bash
python run.py
```

The API will be available at `http://localhost:8000`

**API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Default Credentials

After running `setup.py`, you can log in with these credentials:
You can use the credentials set in the `.env` to login

---

## About

**Project:** RAG Fortress  
**Author:** Nurudeen Habibu  
**GitHub:** [nurudeen19/rag-fortress](https://github.com/nurudeen19/rag-fortress)  
**LinkedIn:** https://www.linkedin.com/in/nurudeen-habibu/  
**License:** MIT

RAG Fortress is an open-source, flexible, and secure Retrieval-Augmented Generation platform with support for multiple LLMs, vector stores, embedding providers, and custom security layers.

---

## Troubleshooting

### "uv: command not found"
Ensure `uv` is installed and added to your PATH. Restart your terminal after installation.

### "Python 3.11+ not found"  
Install Python 3.11 or higher from [python.org](https://www.python.org)

### Module not found
Ensure you've run `uv sync` and activated the virtual environment.

### Database connection issues
Verify your database settings in `.env` and ensure your database server is running.

### Migration errors
Try running migrations individually: `python migrate.py upgrade`

### Partial setup / Reset

If `python setup.py` exits early or seeding fails and you want to start over, you can reset the database and re-run setup:

- **Clear database (recommended):**
```bash
python setup.py --clear-db
```
This command will prompt you to confirm by typing `yes` before dropping all tables.

- **Drop tables helper:**
```bash
python drop_tables.py
```
Run this only if you know what will be removed — it will delete all tables/data.

- **See available setup commands / flags:**
```bash
python setup.py --help
```

Use the `--verify` flag to check whether the setup completed successfully after re-running.

---

## Next Steps

- Read [README.md](../README.md) for full project overview
- Check [docs/](../docs/) for detailed documentation
- Visit [Issues](https://github.com/nurudeen19/rag-fortress/issues) for support
