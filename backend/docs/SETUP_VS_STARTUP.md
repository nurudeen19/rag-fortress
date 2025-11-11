# Setup vs Startup - Deployment Strategy

## Overview

The application distinguishes between **first-time setup** and **regular startup** to avoid running migrations and seeders on every app restart.

```
FIRST-TIME SETUP         vs         REGULAR STARTUP
(Once on deployment)                (Every app restart)

1. Run migrations                   1. Database (tables exist)
2. Run seeders                      2. Recover pending jobs
3. Initialize components           3. Initialize components
4. Ready to serve requests         4. Ready to serve requests
```

## Two Different Flows

### Flow 1: Setup (First-Time Deployment)

```
python setup.py
    ├─ Step 1: Database migrations (Alembic)
    ├─ Step 2: Database seeding (SEEDERS)
    ├─ Step 3: Verification
    └─ Ready for production
```

**When to use:**
- Initial deployment
- Major database schema changes
- Need to reset database and seed from scratch

**What it does:**
1. Runs `alembic upgrade head` (apply all pending migrations)
2. Runs all seeders in order: roles_permissions → departments → admin → jobs → knowledge_base
3. Verifies all required tables exist
4. Creates initial job queue entry

**What it does NOT do:**
- Does NOT start the application
- Does NOT recover pending jobs (none exist yet)
- Must be run ONCE before first app startup

### Flow 2: Startup (Regular App Restart)

```
python run.py
    ├─ FastAPI lifespan startup
    ├─ StartupController.initialize()
    │  ├─ Database connection (tables already exist)
    │  ├─ Recover pending jobs from DB
    │  ├─ Initialize embeddings
    │  ├─ Initialize job queue
    │  └─ Initialize email client
    └─ Ready to serve requests
```

**When to use:**
- Every regular app restart
- After deployment
- Development restarts

**What it does:**
1. Connects to existing database (no migrations)
2. Recovers pending jobs and reschedules them
3. Initializes critical components
4. Serves requests

**What it does NOT do:**
- Does NOT run migrations (assumes they've been applied)
- Does NOT run seeders (assumes data already seeded)
- Assumes database is already set up

## Initialization Order

Both flows initialize components in this order:

```
1. DATABASE        (required by everything)
   ├─ Create engine
   ├─ Create tables
   └─ Create session factory

2. JOB QUEUE       (for processing tasks)
   ├─ Start APScheduler
   ├─ Recover pending jobs from DB
   └─ Reschedule for execution

3. EMBEDDINGS      (for vector operations)
   ├─ Initialize provider
   └─ Test with sample embedding

4. VECTOR STORE    (future)
   └─ Uses embeddings

5. LLM             (optional AI operations)
   ├─ Initialize LLM provider
   └─ Initialize fallback LLM

6. EMAIL           (optional notifications)
   ├─ Initialize client
   └─ Verify credentials
```

## Database State Across Flows

### Before Setup
```
Database: Empty
Files: Not uploaded
Jobs: None
```

### After Setup
```
Database: All tables created
Tables:
  - users (admin user created)
  - roles (admin, manager, user, executive)
  - permissions (CRUD for resources)
  - departments (created)
  - jobs (initial ingestion job created with status=PENDING)
  - file_uploads (empty)
  - ...other tables...
```

### During Regular Startup
```
Database: Unchanged (no migrations/seeding)
Jobs: Any PENDING from setup or previous runs
     → Load from DB
     → Reschedule with JobManager
     → Ready for processing
```

### After File Upload (While Running)
```
Database: New job record inserted
Jobs:     status=PENDING → status=PROCESSING → status=COMPLETED/FAILED
```

### After App Crash (Before Next Startup)
```
Database: Job record still exists (possibly status=PROCESSING)
Jobs:     Recovered and rescheduled on next startup
```

## Implementation

### setup.py - First-Time Setup

```bash
# First-time setup
python setup.py
```

Options:
```bash
# Setup only (verify existing setup)
python setup.py --verify

# Skip seeding, only run migrations
python setup.py --skip-seeders
```

**What it runs:**
1. `alembic upgrade head` - Apply migrations
2. All seeders in order - Populate initial data
3. Verification - Confirm tables exist

### run.py - Regular Startup

```bash
# Regular app startup
python run.py
```

**What it does:**
1. StartupController.initialize() in this order:
   - Database (uses existing tables)
   - Job Queue (recovers pending jobs)
   - Embeddings
   - Email
2. FastAPI starts serving requests

**Doesn't run:**
- Migrations (assumes applied)
- Seeders (assumes already seeded)

## Seeder Order (in setup.py)

Seeders run in this critical order:

1. **roles_permissions** (MUST BE FIRST)
   - Creates roles: admin, manager, user, executive
   - Creates permissions: user:*, document:*, settings:*
   - Other seeders depend on these

2. **departments**
   - Creates organizational structure
   - Referenced by admin seeder

3. **admin**
   - Creates initial admin user
   - Uses roles from step 1
   - Uses departments from step 2

4. **jobs**
   - Creates initial data ingestion job
   - status=PENDING (ready for processing)
   - Uses database from previous steps

5. **knowledge_base**
   - Initializes vector store
   - Prepares for file ingestion

## Job Queue Flow

### Setup Phase
```python
# setup.py runs JobsSeeder
job = Job(
    job_type=FILE_INGESTION,
    status=PENDING,
    reference_id=0,       # System job
    reference_type="system",
    payload=None,
    max_retries=3,
)
# Saved to database
```

### Startup Phase
```python
# startup.py initializes job queue
job_integration.recover_and_schedule_pending()
  ├─ Query: SELECT * FROM jobs WHERE status=PENDING
  ├─ For each job: Schedule with JobManager
  └─ Ready for processing
```

### Processing Phase
```python
# JobManager executes job
_job_wrapper(job_id, handler)
  ├─ mark_processing()
  ├─ Execute handler
  ├─ mark_completed() or mark_failed(retry=True)
  └─ Update database
```

## Decision Tree: Setup or Startup?

```
Is this a fresh deployment?
├─ YES → Run: python setup.py
│        (One-time: migrations + seeders)
│        Then run: python run.py
│
└─ NO → Run: python run.py
        (Every restart: recovery + init)
```

## Benefits of This Approach

✅ **No overhead** - Startup doesn't run expensive migrations/seeders  
✅ **Easy recovery** - Pending jobs loaded automatically  
✅ **Clear separation** - Setup is one-time, startup is regular  
✅ **Consistent order** - Components initialize in predictable order  
✅ **Scalable** - Can add more seeders without affecting startup  
✅ **Safe** - Migrations/seeders never accidentally run twice  

## Troubleshooting

### Tables don't exist after startup
**Problem:** Forgot to run setup.py
```bash
Solution: python setup.py
```

### Pending jobs not recovering
**Problem:** Job queue recovery failed
```bash
Check logs for: "Job queue initialized (recovered X jobs)"
If 0 jobs: That's expected if no jobs are pending
```

### Setup fails at migration step
**Problem:** Alembic not installed or migration issue
```bash
Solution: pip install alembic
        Check migrations for syntax errors
        Run: alembic heads (to verify migration chain)
```

### Setup fails at seeding step
**Problem:** Unique constraint violation
```bash
Solution: This means data already exists
        That's idempotent behavior (expected)
        Check --verify flag to see current state
```

## Production Deployment Checklist

- [ ] Run `python setup.py` once on first deployment
- [ ] Verify output: "✓ SETUP COMPLETE"
- [ ] Check database tables created: `python setup.py --verify`
- [ ] Start app: `python run.py`
- [ ] Monitor logs for: "✓ Application initialization completed"
- [ ] Check job queue: "recovered X pending jobs"
- [ ] Verify embeddings initialized
- [ ] Verify email configured (or warning is OK)
- [ ] Test file upload → job creation → processing

## Summary

**Setup (python setup.py):**
- One-time deployment operation
- Runs migrations + all seeders
- Creates initial database state
- Creates initial job queue entry

**Startup (python run.py):**
- Regular operation (every restart)
- Skips migrations/seeders
- Recovers pending jobs
- Initializes components
- Serves requests

This design ensures:
- ✓ Scalability (no migration overhead on each restart)
- ✓ Recovery (pending jobs continue after restart)
- ✓ Clarity (clear when to run what)
- ✓ Safety (no duplicate seeding)
