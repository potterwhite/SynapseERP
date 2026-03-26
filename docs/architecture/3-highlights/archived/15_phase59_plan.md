# Phase 5.9 — PostgreSQL Migration + Docker Compose Deployment

> **⚠️ FOR AI AGENTS**
> This document describes the complete implementation plan for Phase 5.9.
> Phase 5.9 is currently **IN PROGRESS** as of 2026-03-26.
>
> **READ THIS FIRST** before starting any Phase 5.9 work.
> Each step below specifies exactly what to do and includes commit instructions.
> 
> Last updated: 2026-03-26

---

## Overview

**Goal**: Migrate from SQLite to PostgreSQL and containerize the application with Docker Compose.

**Why Phase 5.9 NOW?**
1. Phase 5.7 introduced tag-based filtering, but JSONField `__contains` lookup only works natively in PostgreSQL
2. Current code applies tag filters in Python layer (see db_adapter.py comments) — inefficient at scale
3. Docker Compose is essential for consistent dev/prod environments and multi-service orchestration
4. PostgreSQL enables connection pooling, better concurrency for multi-user phase

**Key Deliverables:**
- `docker-compose.yml` with PostgreSQL + Django + Nginx + Frontend services
- Updated `settings.py` supporting both SQLite (dev) and PostgreSQL (prod) via environment variables
- One-command local dev setup: `docker-compose up`
- Data migration script: SQLite → PostgreSQL
- Optimized DB adapter with native JSON queries for PostgreSQL

---

## Current State Analysis

### Database Configuration (SQLite)
- Location: `backend/synapse_project/settings.py` (lines 96-101)
- Current: Hardcoded SQLite path
- ORM: Django 5.x with BigAutoField
- Migrations: 12 files across 5 apps (synapse_auth, synapse_attendance, synapse_dashboard, synapse_pm, synapse_bom_analyzer)

### PM Models
- **Project**: 14 fields (id, name, full_name, status, para_type, vault_path, deadline, created, **tags** (JSONField), vault_mtime, synced_at)
- **Task**: 12 fields (id, uuid, name, project_id, status, priority, created, deadline, estimated_hours, depends_on (M2M), vault_path, vault_mtime, synced_at)
- **TimeEntry**: 8 fields (id, task_id, date, description, start_time, end_time, duration_minutes, source_note_path)
- **SyncMeta**: 3 fields (key, value, updated_at)

### Current Dependencies
- Backend: Django 5.0, DRF 3.15, Gunicorn, pandas, openpyxl, python-dotenv, etc.
- **Missing**: `psycopg2-binary`, `dj-database-url` (both required for PostgreSQL)

### Deployment Templates (existing)
- `backend/deploy/nginx.conf.template` — Nginx reverse proxy, static file serving
- `backend/deploy/synapse.service.template` — Systemd service for Gunicorn
- `backend/deploy/synapse.socket.template` — Unix socket management

### Frontend Configuration
- Vite dev server on `:5173` with proxy to `:8000`
- No changes needed for Phase 5.9 (API remains `/api/*`)

---

## Implementation Steps

### STEP 1: Add PostgreSQL Dependencies
**Estimated time**: 5 min

#### File: `backend/requirements.txt`

Add these lines (after `gunicorn`):
```
psycopg2-binary>=2.9
dj-database-url>=2.0
```

**Why?**
- `psycopg2-binary`: PostgreSQL driver for Python
- `dj-database-url`: Simplifies DATABASE URL parsing (optional but recommended)

**Commit message**:
```
feat: add PostgreSQL driver and dj-database-url to requirements

- psycopg2-binary for PostgreSQL connectivity
- dj-database-url for DATABASE_URL env var support

Phase 5.9 Step 1 complete.
```

---

### STEP 2: Update Django Settings for PostgreSQL
**Estimated time**: 15 min

#### File: `backend/synapse_project/settings.py`

**Location**: After line 19 (dotenv.load_dotenv) and before line 33 (SECRET_KEY definition)

**Add this function** (if not already present):
```python
def get_db_config():
    """
    Build database configuration based on DB_ENGINE environment variable.
    
    Supports:
    - SQLite (default, dev): requires no credentials
    - PostgreSQL (prod): requires DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
    """
    db_engine = get_env_variable("DB_ENGINE", "django.db.backends.sqlite3")
    
    if db_engine == "django.db.backends.postgresql":
        return {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": get_env_variable("DB_NAME", "synapse_db"),
                "USER": get_env_variable("DB_USER", "synapse_user"),
                "PASSWORD": get_env_variable("DB_PASSWORD", is_required=True),
                "HOST": get_env_variable("DB_HOST", "localhost"),
                "PORT": get_env_variable("DB_PORT", "5432"),
                "CONN_MAX_AGE": 600,
                "OPTIONS": {
                    "connect_timeout": 10,
                }
            }
        }
    else:
        # SQLite (development)
        return {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }

DATABASES = get_db_config()
```

**Replace existing DATABASES block** (lines 96-101) with:
```python
DATABASES = get_db_config()
```

**Why this approach?**
- Backward compatible: SQLite is still default (dev uses no env vars)
- Production safe: PostgreSQL requires explicit `DB_PASSWORD` env var
- Connection pooling: `CONN_MAX_AGE=600` for long-lived connections
- Timeout protection: `connect_timeout=10` sec

**Commit message**:
```
feat: add PostgreSQL support to Django settings

- New get_db_config() function selects SQLite or PostgreSQL based on DB_ENGINE env var
- PostgreSQL config includes connection pooling (CONN_MAX_AGE=600)
- Backward compatible: SQLite remains default for dev
- Production: set DB_ENGINE, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT in .env

Phase 5.9 Step 2 complete.
```

---

### STEP 3: Create Docker Directory Structure
**Estimated time**: 10 min

#### Create directory: `docker/`

```bash
mkdir -p docker/nginx
touch docker/.dockerignore
touch docker/entrypoint.sh
touch docker/nginx/nginx.conf
```

Structure:
```
docker/
├── .dockerignore
├── entrypoint.sh
├── Dockerfile              (will create next step)
├── Dockerfile.frontend     (will create next step)
└── nginx/
    └── nginx.conf          (will create next step)
```

**Commit message**:
```
chore: create docker directory structure

Phase 5.9 Step 3 preparation.
```

---

### STEP 4: Write Dockerfile (Backend)
**Estimated time**: 15 min

#### File: `docker/Dockerfile`

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY backend/src /app/src
COPY backend/synapse_project /app/synapse_project
COPY backend/manage.py /app/
COPY backend/.env.docker /app/.env || true

# Set PYTHONPATH for importability of synapse_* packages
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Copy entrypoint
COPY docker/entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
```

**Key points:**
- Base: Python 3.12-slim (minimal, ~200MB)
- Dependencies: `postgresql-client` for `pg_restore`, `netcat` for health checks
- PYTHONPATH: ensures `synapse_*` apps are importable
- Entrypoint: custom script for migrations + startup (Step 5)

**Commit message**:
```
build: create Dockerfile for Django backend

- Python 3.12-slim base image
- Installs psycopg2 and other dependencies
- Configures PYTHONPATH for synapse_* packages
- Uses entrypoint.sh for initialization

Phase 5.9 Step 4 complete.
```

---

### STEP 5: Write Entrypoint Script
**Estimated time**: 10 min

#### File: `docker/entrypoint.sh`

```bash
#!/bin/bash
set -e

echo "[entrypoint] Waiting for PostgreSQL..."
while ! nc -z "${DB_HOST:-postgres}" "${DB_PORT:-5432}"; do
  sleep 1
done
echo "[entrypoint] PostgreSQL is ready!"

echo "[entrypoint] Running migrations..."
python manage.py migrate --noinput

echo "[entrypoint] Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "[entrypoint] Starting Gunicorn..."
exec gunicorn \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --access-logfile - \
  --error-logfile - \
  synapse_project.wsgi:application
```

**Key points:**
- Waits for PostgreSQL to be ready before migrations
- Runs `migrate` + `collectstatic` automatically
- Starts Gunicorn with 3 workers (configurable)

**Commit message**:
```
build: add docker entrypoint.sh for Django initialization

- Waits for PostgreSQL readiness (netcat healthcheck)
- Automatically runs migrations and collectstatic
- Starts Gunicorn with 3 workers

Phase 5.9 Step 5 complete.
```

---

### STEP 6: Write Dockerfile (Frontend)
**Estimated time**: 10 min

#### File: `docker/Dockerfile.frontend`

```dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy source
COPY frontend/ .

# Dev server port
EXPOSE 5173

# Start dev server (accessible from host)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

**Key points:**
- `npm ci` instead of `npm install` (faster, more reliable in Docker)
- `--host 0.0.0.0` makes Vite dev server accessible from docker host
- Mounts as volume in docker-compose for hot reload

**Commit message**:
```
build: create Dockerfile for Vue 3 frontend

- Node 20 Alpine base
- Uses npm ci for reproducible installs
- Vite dev server on 0.0.0.0:5173 for docker accessibility

Phase 5.9 Step 6 complete.
```

---

### STEP 7: Write docker-compose.yml
**Estimated time**: 20 min

#### File: `docker-compose.yml` (project root)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: synapse_postgres
    environment:
      POSTGRES_DB: ${DB_NAME:-synapse_db}
      POSTGRES_USER: ${DB_USER:-synapse_user}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-synapse_user}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: synapse_backend
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DJANGO_SETTINGS_MODULE: synapse_project.settings
      DB_ENGINE: django.db.backends.postgresql
      DB_NAME: ${DB_NAME:-synapse_db}
      DB_USER: ${DB_USER:-synapse_user}
      DB_PASSWORD: ${DB_PASSWORD:-changeme}
      DB_HOST: postgres
      DB_PORT: 5432
      DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY:-dev-secret-key-change-in-production}
      DJANGO_DEBUG: ${DJANGO_DEBUG:-False}
      DJANGO_ALLOWED_HOSTS: ${DJANGO_ALLOWED_HOSTS:-localhost,127.0.0.1}
    volumes:
      - ./backend/src:/app/src
      - ./backend/synapse_project:/app/synapse_project
      - static_volume:/app/staticfiles
    ports:
      - "8000:8000"
    expose:
      - "8000"

  frontend:
    build:
      context: .
      dockerfile: docker/Dockerfile.frontend
    container_name: synapse_frontend
    volumes:
      - ./frontend/src:/app/src
      - ./frontend/public:/app/public
      - /app/node_modules
    ports:
      - "5173:5173"
    expose:
      - "5173"

  nginx:
    image: nginx:alpine
    container_name: synapse_nginx
    depends_on:
      - backend
      - frontend
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/app/staticfiles:ro
    ports:
      - "80:80"
    expose:
      - "80"

volumes:
  postgres_data:
  static_volume:
```

**Key points:**
- `depends_on` with `condition: service_healthy` ensures PostgreSQL is ready
- Environment variables from `.env` file (with defaults)
- Volumes for code hot-reload and data persistence
- Healthcheck on PostgreSQL for safe startup sequencing
- Nginx orchestrates backend + frontend

**Create `.env` file** in project root if not exists:
```bash
# Database
DB_NAME=synapse_db
DB_USER=synapse_user
DB_PASSWORD=secure_password_here
DB_HOST=postgres
DB_PORT=5432

# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

**Commit message**:
```
build: add docker-compose.yml with PostgreSQL + backend + frontend + nginx

- PostgreSQL 16 Alpine with healthcheck
- Backend Django/Gunicorn with auto-migration
- Frontend Vue 3 dev server
- Nginx reverse proxy
- Volumes for data persistence and code hot-reload
- Environment variable support via .env

Phase 5.9 Step 7 complete.
```

---

### STEP 8: Write Nginx Configuration
**Estimated time**: 15 min

#### File: `docker/nginx/nginx.conf`

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 20M;

    upstream synapse_backend {
        server backend:8000;
    }

    upstream synapse_frontend {
        server frontend:5173;
    }

    server {
        listen 80;
        server_name _;

        # Suppress favicon 404 logs
        location = /favicon.ico {
            access_log off;
            log_not_found off;
        }

        # Django static files (collected by collectstatic)
        location /static/ {
            alias /app/staticfiles/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # Backend API and admin
        location ~ ^/(api|admin|i18n)/ {
            proxy_pass http://synapse_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Frontend SPA (dev mode)
        location / {
            proxy_pass http://synapse_frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

**Key points:**
- Separates backend API (`/api`, `/admin`, `/i18n`) from frontend
- Static files from Django `collectstatic` output
- Frontend served from Vite dev server in dev mode
- Proper caching headers for static assets

**Commit message**:
```
build: add nginx configuration for Docker container

- Proxies /api, /admin, /i18n to Django backend
- Serves /static from collected Django static files
- Proxies frontend requests to Vite dev server
- Proper caching and security headers

Phase 5.9 Step 8 complete.
```

---

### STEP 9: Create .dockerignore
**Estimated time**: 5 min

#### File: `.dockerignore`

```
# Git
.git
.gitignore

# Python
__pycache__
*.pyc
*.pyo
*.pyd
.Python
venv/
.venv
env/
.env
*.egg-info
dist
build

# Node
node_modules
npm-debug.log
pnpm-lock.yaml
dist

# IDE
.vscode
.idea
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project
db.sqlite3
.claude
docs
tests
.github
README.md
LICENSE
```

**Commit message**:
```
build: add .dockerignore to exclude unnecessary files

Phase 5.9 Step 9 complete.
```

---

### STEP 10: Optimize DB Adapter for PostgreSQL
**Estimated time**: 20 min

#### File: `backend/src/synapse_pm/adapters/db_adapter.py`

**Location**: In `list_projects()` method (around line 128)

**Replace the current implementation** with PostgreSQL-optimized version:

```python
def list_projects(self, *, status: str | None = None, tags: list[str] | None = None) -> list[dict[str, Any]]:
    """
    Return a list of project dicts.
    
    On PostgreSQL: Use native JSONField @> operator for tag filtering.
    On SQLite: Filter in Python (backward compatible).
    """
    from django.db import connection
    
    qs = Project.objects.prefetch_related("tasks", "tasks__time_entries")
    if status:
        qs = qs.filter(status=status)
    
    # PostgreSQL optimization: use native JSON containment operator
    if tags and connection.vendor == 'postgresql':
        from django.db.models import Q
        
        # Build Q filter: project.tags must contain ALL specified tags
        q_filters = Q()
        for tag in tags:
            q_filters &= Q(tags__contains=[tag])
        
        qs = qs.filter(q_filters)
        result = [self._project_to_dict(p) for p in qs]
    else:
        # SQLite: fetch all and filter in Python (existing behavior)
        result = [self._project_to_dict(p) for p in qs]
        if tags:
            result = [
                d for d in result
                if all(t in (d.get("tags") or []) for t in tags)
            ]
    
    return result
```

**Add comment above the method**:
```python
# Phase 5.9: PostgreSQL JSON optimization
# PostgreSQL supports native JSONField queries via @> operator,
# while SQLite requires Python-layer filtering.
# This method detects the database backend and applies optimal strategy.
```

**Commit message**:
```
perf: optimize tag filtering for PostgreSQL with native JSON queries

- PostgreSQL: Use JSONField @> operator for efficient server-side filtering
- SQLite: Fallback to Python filtering (backward compatible)
- Adds connection.vendor detection to choose optimal path
- Improves performance for large project lists with many tags

Phase 5.9 Step 10 complete.
```

---

### STEP 11: Create Migration Test Script
**Estimated time**: 15 min

#### File: `scripts/migrate_sqlite_to_postgres.sh`

```bash
#!/bin/bash
# Migrate data from SQLite to PostgreSQL
# Usage: ./scripts/migrate_sqlite_to_postgres.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "=== SQLite → PostgreSQL Migration ==="
echo ""

# Step 1: Dump SQLite data
echo "[1/5] Exporting SQLite data..."
cd "$BACKEND_DIR"
python manage.py dumpdata --natural-foreign --natural-primary > /tmp/synapse_backup.json
echo "✓ Data exported to /tmp/synapse_backup.json"
echo ""

# Step 2: Verify PostgreSQL is running
echo "[2/5] Checking PostgreSQL connection..."
if ! docker-compose exec -T postgres pg_isready -U synapse_user > /dev/null 2>&1; then
    echo "✗ PostgreSQL not ready. Start it with: docker-compose up postgres"
    exit 1
fi
echo "✓ PostgreSQL is ready"
echo ""

# Step 3: Run migrations
echo "[3/5] Running migrations on PostgreSQL..."
docker-compose exec -T backend python manage.py migrate --noinput
echo "✓ Migrations completed"
echo ""

# Step 4: Load data
echo "[4/5] Loading data into PostgreSQL..."
docker-compose exec -T backend python manage.py loaddata /tmp/synapse_backup.json
echo "✓ Data imported"
echo ""

# Step 5: Verify
echo "[5/5] Verifying data integrity..."
SQLITE_COUNT=$(sqlite3 "$BACKEND_DIR/db.sqlite3" "SELECT COUNT(*) FROM synapse_pm_project;")
POSTGRES_COUNT=$(docker-compose exec -T postgres psql -U synapse_user -d synapse_db -t -c "SELECT COUNT(*) FROM synapse_pm_project;")

echo "SQLite Project count:     $SQLITE_COUNT"
echo "PostgreSQL Project count: $POSTGRES_COUNT"

if [ "$SQLITE_COUNT" -eq "$POSTGRES_COUNT" ]; then
    echo "✓ Data integrity verified!"
else
    echo "✗ Mismatch detected! Review /tmp/synapse_backup.json"
    exit 1
fi
```

Make it executable:
```bash
chmod +x scripts/migrate_sqlite_to_postgres.sh
```

**Commit message**:
```
script: add SQLite → PostgreSQL migration helper

- Exports SQLite data to JSON
- Waits for PostgreSQL readiness
- Runs Django migrations
- Imports data into PostgreSQL
- Verifies data integrity by count

Usage: ./scripts/migrate_sqlite_to_postgres.sh

Phase 5.9 Step 11 complete.
```

---

### STEP 12: Update CLAUDE.md with Phase 5.9 Instructions
**Estimated time**: 15 min

#### File: `CLAUDE.md`

**Add this section after "### Development"**:

```markdown
### Docker (Phase 5.9)
```bash
docker-compose build       # Build all images
docker-compose up -d       # Start all services (PostgreSQL + Django + Nginx + Vue)
docker-compose logs -f     # View all logs
docker-compose down        # Stop all services
docker-compose down -v     # Stop + remove volumes (clean slate)
```

**Local development with Docker:**
1. Copy `.env.example` to `.env` (if exists) or create minimal `.env`:
   ```
   DB_PASSWORD=dev_password
   DJANGO_SECRET_KEY=dev_secret_key
   ```
2. `docker-compose up -d` — starts all services
3. `docker-compose exec backend python manage.py createsuperuser` — create admin
4. Visit `http://localhost` — Nginx proxies to Vue frontend
5. Logs: `docker-compose logs -f backend` / `docker-compose logs -f frontend`

**Data migration (SQLite → PostgreSQL in Docker):**
```bash
docker-compose up postgres -d  # Start PostgreSQL only
docker-compose exec backend python manage.py migrate --noinput
sqlite3 backend/db.sqlite3 '.mode insert' 'SELECT * FROM ...' | ...
# (Or use the helper script: ./scripts/migrate_sqlite_to_postgres.sh)
```

**Production deployment:**
- Use `docker-compose.prod.yml` (not in Phase 5.9, but planned)
- Set strong `DB_PASSWORD`, `DJANGO_SECRET_KEY` in `.env`
- Use external PostgreSQL (RDS / managed service)
- Use reverse proxy (not Nginx container)
```

**Commit message**:
```
docs: add Docker Compose instructions to CLAUDE.md

- Local dev setup with docker-compose
- Data migration procedures
- Notes on production deployment

Phase 5.9 Step 12 complete.
```

---

### STEP 13: Test Locally
**Estimated time**: 30 min (one-time, not code change)

This is a VALIDATION step, not a code commit. But **DO commit the .env example and docker setup**.

**Instructions for testing:**
```bash
# 1. Build images
docker-compose build

# 2. Start services
docker-compose up -d

# 3. Check services are healthy
docker-compose ps
# Expected: all services "Up"

# 4. Verify PostgreSQL
docker-compose exec postgres psql -U synapse_user -d synapse_db -c "SELECT version();"

# 5. Verify Django migrations
docker-compose logs backend | grep "Running migrations"

# 6. Create admin user
docker-compose exec backend python manage.py createsuperuser
# Follow prompts

# 7. Test API
curl http://localhost/api/health/
# Expected: {"status": "ok", ...}

# 8. Test frontend
# Open http://localhost in browser
# Expected: Vue SPA loads, login page appears

# 9. Test login
# Use admin credentials from step 6
# Expected: Dashboard loads, authenticated

# 10. Cleanup
docker-compose down -v
```

**If issues occur:**
- Check logs: `docker-compose logs <service>`
- Rebuild: `docker-compose build --no-cache`
- Reset: `docker-compose down -v && docker-compose up -d`

**Commit message** (after successful testing):
```
test: verify Phase 5.9 Docker Compose setup

- PostgreSQL 16 Alpine connectivity ✓
- Django migrations run successfully ✓
- Gunicorn startup and healthcheck ✓
- Vue frontend loads via Nginx ✓
- Login/authentication flow ✓
- API endpoints accessible ✓

All Phase 5.9 deliverables validated.
```

---

### STEP 14: Update 00_INDEX.md
**Estimated time**: 10 min

Update `docs/architecture/00_INDEX.md`:

1. Change Phase 5.9 status from `⏳` to `✅` (if complete)
2. Add new entry to 14_phase59_plan.md reference
3. Update "Current Progress" table

See `docs/architecture/00_INDEX.md` for exact lines to update.

**Commit message**:
```
docs: mark Phase 5.9 complete in architecture index

- Update status from ⏳ to ✅
- Add reference to 15_phase59_plan.md
- Update current progress table

Phase 5.9 complete!
```

---

## Commit Sequence Summary

Each step above must be committed **separately** with the specified message format.
This ensures atomic, reviewable history and makes rollback possible.

```
STEP 1  → requirements.txt (psycopg2, dj-database-url)
STEP 2  → settings.py (PostgreSQL config)
STEP 3  → docker/ directory creation
STEP 4  → docker/Dockerfile (backend)
STEP 5  → docker/entrypoint.sh (initialization)
STEP 6  → docker/Dockerfile.frontend (Vue)
STEP 7  → docker-compose.yml (orchestration)
STEP 8  → docker/nginx/nginx.conf
STEP 9  → .dockerignore
STEP 10 → db_adapter.py (PostgreSQL optimization)
STEP 11 → scripts/migrate_sqlite_to_postgres.sh
STEP 12 → CLAUDE.md (instructions)
STEP 13 → (testing only, no code commit yet)
STEP 14 → 00_INDEX.md (documentation update)
```

**Total expected commits: 13**

---

## Verification Checklist

After completing all steps, verify:

- [ ] All 13 commits are in git log
- [ ] `docker-compose build` succeeds
- [ ] `docker-compose up -d` starts all services healthy
- [ ] `curl http://localhost/api/health/` returns 200
- [ ] Admin user can be created
- [ ] Vue SPA loads at `http://localhost`
- [ ] Login works with admin credentials
- [ ] PM module (projects, tasks, tags) functional in Docker setup
- [ ] PostgreSQL data persists across `docker-compose down/up`
- [ ] SQLite mode still works: `DJANGO_DEBUG=True ./synapse run` (no Docker)

---

## Next Phases (After 5.9)

**Phase 5.10+**: Planned enhancements (not in scope of Phase 5.9)
- Docker Compose production variant (`docker-compose.prod.yml`)
- Celery task queue for async vault sync
- Redis caching layer
- Kubernetes deployment manifests
- API rate limiting + logging aggregation

---

## References

- Docker Compose docs: https://docs.docker.com/compose/
- PostgreSQL Docker image: https://hub.docker.com/_/postgres
- Django PostgreSQL docs: https://docs.djangoproject.com/en/5.0/ref/databases/#postgresql-notes
- psycopg2 docs: https://www.psycopg.org/
- Gunicorn systemd integration: https://docs.gunicorn.org/en/stable/

