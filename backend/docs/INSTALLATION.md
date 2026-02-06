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
python setup.py --all
```

This command will:
- Run all database migrations
- Load all initial seed data (roles, permissions, admin user, etc.)
- Set up the database schema

**Available setup options:**

```bash
# Run all seeders (full setup)
python setup.py --all

# Run only specific seeders
python setup.py --only-seeder admin,roles_permissions

# Run all seeders except specified ones
python setup.py --skip-seeder departments,jobs,conversations

# View available seeders
python setup.py --list-seeders

# Verify database setup is complete
python setup.py --verify

# Clear database (for recovery/reset)
python setup.py --clear-db
```

**To run seeders separately:**

```bash
# Run all seeders
python run_seeders.py --all

# Run specific seeders
python run_seeders.py --only-seeder admin,roles_permissions

# Skip certain seeders
python run_seeders.py --skip-seeder departments
```

**Available seeders:**
- `admin` - Creates admin user account from environment variables
- `roles_permissions` - Creates system roles and permissions
- `departments` - Creates department records
- `application_settings` - Creates application-level settings
- `jobs` - Creates sample job records
- `knowledge_base` - Creates sample knowledge base entries
- `conversations` - Creates sample conversations
- `activity_logs` - Creates sample activity logs

**Admin seeder configuration:**

The admin seeder reads credentials from environment variables. Set these in `.env` before running setup:
- `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`
- Optional: `ADMIN_FIRSTNAME`, `ADMIN_LASTNAME`

**Note:** Seeders are implemented to be idempotent where possible. If a seeder detects existing records (unique constraints), it will skip or warn rather than duplicate data.

### 6. Start the Server

```bash
# Production mode (no auto-reload)
python startup.py

# Development mode (with auto-reload)
python startup.py --reload
python startup.py --dev

# Set environment via environment variable
ENVIRONMENT=development python startup.py
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

### Installing Development Packages with uv

If you want to install development/testing packages alongside production dependencies:

```bash
uv sync --extra dev
```

This installs additional development tools like:
- Testing frameworks (pytest, coverage)
- Code quality tools (pylint, black, mypy)
- Development utilities

### "Python 3.11+ not found"  
Install Python 3.11 or higher from [python.org](https://www.python.org)

### Package Build Failing (Compilation Error)

If you encounter errors like `error: Microsoft Visual C++ 14.0 is required` or compilation failures during `uv sync` or `pip install`, you need C++ build tools:

**Windows:**
1. Download and install [Visual Studio Installer](https://visualstudio.microsoft.com/visual-studio-installer/)
2. Open Visual Studio Installer and click "Create new" or "Modify"
3. **For a lightweight installation:** Under "Individual components", search for and select:
   - **Windows SDK** (Windows 11 SDK or your Windows version SDK)
   - **MSBuild tools**
   - Click "Install" to proceed
4. **Alternative (full workload):** If you prefer a complete C++ setup, select "Modify" and check "Desktop development with C++" under Workloads
5. Restart your terminal and retry `uv sync`

*Note: Installing individual components (SDK + MSBuild) is recommended for minimal disk space usage.*

**macOS:**
```bash
xcode-select --install
```
This installs Xcode Command Line Tools which includes necessary C++ build tools.

**Linux:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install build-essential

# Fedora/RHEL
sudo dnf install gcc gcc-c++ make

# Arch
sudo pacman -S base-devel
```

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

## Alternative Installation Methods

### Legacy Installation (pip + Chroma)

If you're using **Python 3.11-3.13** and want to use Chroma vector database instead of FAISS, or prefer traditional pip installation, see the [Legacy Installation Guide](INSTALLATION_LEGACY.md).

**Note:** As of December 2025, Chroma is not yet compatible with Python 3.14+. The legacy installation is only for Python 3.11-3.13 users. Python 3.14 support is being worked on by the Chroma team.

---

## Next Steps

- Read [README.md](../README.md) for full project overview
- Check [docs/](../docs/) for detailed documentation
- Visit [Issues](https://github.com/nurudeen19/rag-fortress/issues) for support
