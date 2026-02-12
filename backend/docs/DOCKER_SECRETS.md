# Docker Secrets Guide

This guide explains how to use Docker secrets for secure configuration management in RAG Fortress.

## Table of Contents

- [What are Docker Secrets?](#what-are-docker-secrets)
- [Why Use Secrets?](#why-use-secrets)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Available Secrets](#available-secrets)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

## What are Docker Secrets?

Docker secrets are a secure way to store sensitive data like passwords, API keys, and encryption keys. Instead of storing them in environment variables or `.env` files, secrets are:

- Stored as files in a secure location (`/run/secrets/` in containers)
- Not visible in `docker inspect` output
- Not stored in container images
- Can have restricted file permissions
- Better suited for production deployments

## Why Use Secrets?

### Environment Variables (`.env.docker`)

❌ **Cons:**
- Visible in `docker inspect`
- Risk of committing to version control
- Exposed in process listings
- Harder to rotate/update

✅ **Pros:**
- Simple for development
- Easy to understand
- Quick to set up

### Docker Secrets

✅ **Pros:**
- Not in environment variables
- Not in `docker inspect`
- File permissions controlled by Docker
- External to container images
- Production-ready

❌ **Cons:**
- Slightly more setup
- Requires file management

**Recommendation:** Use `.env.docker` for development, Docker secrets for production.

## Quick Start

### 1. Generate Encryption Keys

```bash
docker compose --profile keygen run --rm keygen
```

Copy the output keys (you'll need them in the next step).

### 2. Create Secrets Files

**Option A: From .env.docker (Automated)**

If you already have values in `.env.docker`:

```powershell
# Windows PowerShell
.\create-secrets.ps1 -FromEnv
```

```bash
# Linux/Mac
chmod +x create-secrets.sh
./create-secrets.sh --from-env
```

**Option B: Interactive**

```powershell
# Windows PowerShell
.\create-secrets.ps1 -Interactive
```

```bash
# Linux/Mac
./create-secrets.sh --interactive
```

**Option C: Manual**

```powershell
# Windows PowerShell
"your_db_password" | Out-File -NoNewline -FilePath secrets/db_password.txt
"your_secret_key" | Out-File -NoNewline -FilePath secrets/secret_key.txt
"your_master_encryption_key" | Out-File -NoNewline -FilePath secrets/master_encryption_key.txt
"your_settings_encryption_key" | Out-File -NoNewline -FilePath secrets/settings_encryption_key.txt
"your_llm_api_key" | Out-File -NoNewline -FilePath secrets/llm_api_key.txt
```

```bash
# Linux/Mac
echo -n 'your_db_password' > secrets/db_password.txt
echo -n 'your_secret_key' > secrets/secret_key.txt
echo -n 'your_master_encryption_key' > secrets/master_encryption_key.txt
echo -n 'your_settings_encryption_key' > secrets/settings_encryption_key.txt
echo -n 'your_llm_api_key' > secrets/llm_api_key.txt

# Secure the files
chmod 600 secrets/*.txt
```

### 3. Verify Secret Files

```bash
# Check files were created
ls -la secrets/

# Verify content (be careful - this shows sensitive data!)
cat secrets/secret_key.txt
```

**Important:** Each file should contain ONLY the secret value with NO trailing newline.

### 4. Update Application to Use Secrets

Your application needs to read from `/run/secrets/` inside containers. The secrets are already defined in `docker-compose.yml` but commented out. You can uncomment the `secrets:` sections in service definitions when ready.

### 5. Remove Secrets from .env.docker

Once you've confirmed secrets are working, remove the sensitive values from `.env.docker`:

```bash
# .env.docker - Remove or comment these:
# SECRET_KEY=...
# MASTER_ENCRYPTION_KEY=...
# SETTINGS_ENCRYPTION_KEY=...
# LLM_API_KEY=...
```

## Detailed Setup

### Secrets Directory Structure

```
backend/
├── secrets/
│   ├── .gitkeep                    # Documentation (tracked)
│   ├── postgres_password.txt       # Database password (gitignored)
│   ├── secret_key.txt              # App secret (gitignored)
│   ├── master_encryption_key.txt   # Master key (gitignored)
│   ├── settings_encryption_key.txt # Settings key (gitignored)
│   ├── openai_api_key.txt          # OpenAI key (gitignored)
│   └── google_api_key.txt          # Google key (gitignored)
├── docker-compose.yml
├── create-secrets.ps1              # Windows helper script
└── create-secrets.sh               # Linux/Mac helper script
```

### docker-compose.yml Configuration

Secrets are defined at the top level:

```yaml
secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
  secret_key:
    file: ./secrets/secret_key.txt
  # ... more secrets
```

Then referenced in services:

```yaml
services:
  backend:
    secrets:
      - secret_key
      - master_encryption_key
      - settings_encryption_key
      - openai_api_key
```

Inside the container, secrets are available at `/run/secrets/<secret_name>`:

```python
# Python example
with open('/run/secrets/secret_key', 'r') as f:
    secret_key = f.read().strip()
```

## Available Secrets

| Secret Name | Environment Variable | Description | Required |
|-------------|---------------------|-------------|----------|
| `secret_key` | `SECRET_KEY` | Application secret key (Fernet) | ✅ Yes |
| `master_encryption_key` | `MASTER_ENCRYPTION_KEY` | Master encryption key (Fernet) | ✅ Yes |
| `settings_encryption_key` | `SETTINGS_ENCRYPTION_KEY` | Settings encryption key (Fernet) | ✅ Yes |
| `db_password` | `DB_PASSWORD` | PostgreSQL database password | ✅ Yes |
| `llm_api_key` | `LLM_API_KEY` | Primary LLM API key | ⚠️ Optional |
| `fallback_llm_api_key` | `FALLBACK_LLM_API_KEY` | Fallback LLM API key | ⚠️ Optional |
| `classifier_llm_api_key` | `CLASSIFIER_LLM_API_KEY` | Intent classifier API key | ⚠️ Optional |
| `internal_llm_api_key` | `INTERNAL_LLM_API_KEY` | Internal LLM API key | ⚠️ Optional |
| `embedding_api_key` | `EMBEDDING_API_KEY` | Embedding model API key | ⚠️ Optional |
| `reranker_api_key` | `RERANKER_API_KEY` | Reranker API key | ⚠️ Optional |
| `vector_db_api_key` | `VECTOR_DB_API_KEY` | Vector database API key | ⚠️ Optional |
| `smtp_password` | `SMTP_PASSWORD` | SMTP server password | ⚠️ Optional |
| `admin_password` | `ADMIN_PASSWORD` | Default admin password | ⚠️ Optional |

## Security Best Practices

### 1. File Permissions

Always restrict access to secret files:

```bash
# Linux/Mac
chmod 600 secrets/*.txt
chown $(whoami):$(whoami) secrets/*.txt

# Verify
ls -la secrets/
# Should show: -rw------- (only owner can read/write)
```

### 2. Never Commit Secrets

The `secrets/` directory is gitignored except for `.gitkeep`. Verify:

```bash
git status
# secrets/*.txt should NOT appear in untracked files
```

### 3. Rotate Secrets Regularly

Update secret files and restart services:

```bash
# Update secret file
echo -n 'new_secret_value' > secrets/secret_key.txt

# Restart affected services
docker compose restart backend
```

### 4. Backup Secrets Securely

**Do NOT** backup secrets to version control. Use:
- Encrypted password managers (1Password, Bitwarden)
- Secure secret management systems (HashiCorp Vault, AWS Secrets Manager)
- Encrypted backups with proper access controls

### 5. Separate Secrets by Environment

Use different secrets for development, staging, and production:

```bash
# Example: separate secret directories
secrets/dev/
secrets/staging/
secrets/prod/

# Point docker-compose.yml to the right directory
```

### 6. Audit Secret Access

Monitor who accesses secrets:

```bash
# Linux: Enable auditing
sudo auditctl -w /path/to/secrets/ -p rwa -k secrets_access

# Check audit log
sudo ausearch -k secrets_access
```

## Troubleshooting

### Secret file not found

**Error:** `secret not found: postgres_password`

**Solution:**
1. Verify file exists: `ls -la secrets/postgres_password.txt`
2. Check file has content: `cat secrets/postgres_password.txt`
3. Ensure no extra extensions: should be `.txt` not `.txt.txt`

### Secret has trailing newline

**Error:** Authentication fails, keys don't work

**Solution:** Secrets must have NO trailing newline:

```bash
# Wrong (adds newline)
echo "secret_value" > secrets/secret_key.txt

# Correct (no newline)
echo -n "secret_value" > secrets/secret_key.txt

# PowerShell (no newline)
"secret_value" | Out-File -NoNewline -FilePath secrets/secret_key.txt
```

### Permission denied

**Error:** `Permission denied: '/run/secrets/secret_key'`

**Solution:**
1. Check file permissions: `chmod 600 secrets/secret_key.txt`
2. Verify secret is mounted: `docker compose config` should show the secret
3. Check if secret is declared in service: service needs `secrets:` section

### Secret not updated in container

**Error:** Changes to secret file not reflected

**Solution:**
```bash
# Secrets are read at container start, so restart:
docker compose restart backend

# Or recreate:
docker compose up -d --force-recreate backend
```

### Using both .env and secrets

**Warning:** If a value exists in both `.env.docker` AND a secret file, the environment variable takes precedence.

**Solution:** Remove the variable from `.env.docker` when using secrets.

## Migration from .env.docker

### Step-by-Step Migration

1. **Backup current configuration:**
   ```bash
   cp .env.docker .env.docker.backup
   ```

2. **Create secrets from .env.docker:**
   ```bash
   ./create-secrets.sh --from-env
   ```

3. **Verify secrets were created:**
   ```bash
   ls -la secrets/
   ```

4. **Test with secrets:**
   ```bash
   # Start services with secrets
   docker compose up -d
   
   # Check logs for errors
   docker compose logs backend
   ```

5. **Remove sensitive values from .env.docker:**
   ```bash
   # Edit .env.docker and remove or comment:
   # SECRET_KEY=...
   # MASTER_ENCRYPTION_KEY=...
   # etc.
   ```

6. **Final verification:**
   ```bash
   # Restart to ensure no fallback to .env.docker
   docker compose restart backend
   docker compose logs backend
   ```

## Advanced: External Secrets

For production, consider external secret management:

### AWS Secrets Manager

```yaml
secrets:
  postgres_password:
    external: true
    name: prod/ragfortress/postgres_password
```

### HashiCorp Vault

```yaml
secrets:
  postgres_password:
    external: true
    name: vault:secret/data/ragfortress#postgres_password
```

### Docker Swarm Secrets

```bash
# Create secret in Swarm
echo "my_secret" | docker secret create postgres_password -

# Reference in docker-compose.yml
secrets:
  postgres_password:
    external: true
```

## References

- [Docker Secrets Documentation](https://docs.docker.com/engine/swarm/secrets/)
- [Docker Compose Secrets](https://docs.docker.com/compose/compose-file/09-secrets/)
- [12-Factor App: Config](https://12factor.net/config)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
