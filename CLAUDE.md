# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Requirement
- All source code (with comments) must be in English.
- Communicate with me in Chinese.
- In Claude code, do not end interactions arbitrarily; always use UserAskQuestion to continuously prompt the user for input.

## Commands

All common operations are handled by the `./synapse` orchestrator script at the project root.

### Setup & Run
```bash
./synapse prepare          # Full setup: venv, pip install, migrate, compile translations, npm install
./synapse run              # Start Django dev server (http://127.0.0.1:8000)
./synapse frontend:run     # Start Vue dev server (http://localhost:5173)
./synapse run:all          # Start both backend and frontend in parallel
./synapse superuser        # Create Django admin superuser
```

### Development
```bash
./synapse dev:migrate      # makemigrations + migrate
./synapse dev:test         # Run Django test suite
./synapse dev:makemessages # Update .po translation files (zh_Hans)
./synapse dev:compilemessages # Compile .mo translation files
```

### Frontend
```bash
cd frontend && npm run dev      # Vite dev server
cd frontend && npm run build    # Production build (vue-tsc + vite)
```

### Docker Compose (Phase 5.9)

```bash
# First-time setup:
cp .env.docker.example .env.docker
# Edit .env.docker: set DJANGO_SECRET_KEY and DB_PASSWORD

./synapse docker:up              # Build images + start all services (postgres + backend + nginx)
./synapse docker:down            # Stop and remove containers (volumes preserved)
./synapse docker:clean           # ⚠️  Destroy containers + volumes + images (data loss!)
./synapse docker:logs            # Tail all service logs
./synapse docker:logs backend    # Tail backend logs only
./synapse docker:shell           # Open shell in backend container

# Create admin user (first-time):
./synapse docker:shell
# Inside container: python manage.py createsuperuser
```

**Docker services:**
- `postgres` — PostgreSQL 16 (data persisted in `postgres_data` volume)
- `backend` — Django/Gunicorn on :8000 (internal only, not exposed to host)
- `nginx` — Nginx on :80 (public), serves Vue SPA + proxies `/api/` to backend

**Docker environment variables** — stored in `.env.docker` (gitignored):

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `DJANGO_SECRET_KEY` | ✅ | — | Long random string |
| `DB_PASSWORD` | ✅ | — | PostgreSQL password |
| `DB_NAME` | — | `synapse_db` | |
| `DB_USER` | — | `synapse_user` | |
| `NGINX_PORT` | — | `80` | Change if port 80 is taken |
| `GUNICORN_WORKERS` | — | `3` | |
| `OBSIDIAN_VAULT_PATH` | — | — | Optional: set to host path; auto-mounted at `/vault` in container |

### Production
```bash
sudo ./synapse deploy      # Interactive deployment: Nginx + Gunicorn + Systemd
./synapse clean            # Destructive reset: removes .venv, db.sqlite3, node_modules, dist
```

### Running a single Django test
```bash
cd backend && ../.venv/bin/python manage.py test synapse_pm.tests.TestClassName.test_method_name
```

## Architecture

### Stack
- **Backend**: Django 5.x + Django REST Framework, Python 3.10+ (3.12 recommended)
- **Frontend**: Vue 3 (Composition API) + TypeScript + Vite 6
- **UI**: Naive UI (TypeScript-native component library)
- **State**: Pinia 3 stores
- **HTTP**: Axios with `/api` proxy to Django backend in dev
- **Database**: SQLite (dev) → PostgreSQL (prod)
- **Prod serving**: Gunicorn (WSGI) behind Nginx, managed by Systemd

### Backend Module Structure

Django apps live in `backend/src/`. Each app is a pluggable module:

| App | Purpose |
|-----|---------|
| `synapse/` | Core framework metadata and shared utilities |
| `synapse_api/` | Health check and dashboard REST endpoints |
| `synapse_dashboard/` | `Notification` model (Markdown content, displayed on dashboard) |
| `synapse_attendance/` | Excel attendance file parser with TOML rules engine |
| `synapse_bom_analyzer/` | Multi-file BOM aggregation |
| `synapse_pm/` | Project Management: `Project`, `Task`, `TimeEntry` models (Phase 2, in progress) |

URL routing is in `backend/synapse_project/urls.py` (top-level) and `api_urls.py` (REST API at `/api/`).

### PM Module Backend Modes

`synapse_pm` supports two switchable backends via `SYNAPSE_PM_BACKEND` env var:
- `database` (default) — standard Django ORM
- `vault` — reads/writes Obsidian markdown vault at `OBSIDIAN_VAULT_PATH`

The vault mode parses Obsidian PARA-structured notes; see `docs/architecture/reference/obsidian_parsing_rules.md` for regex rules.

### Frontend Structure

```
frontend/src/
├── api/client.ts        # Axios instance with interceptors
├── api/types.ts         # TypeScript API response types
├── router/index.ts      # Route definitions
├── stores/app.ts        # Global state (notifications, modules)
├── stores/auth.ts       # Auth session state
├── views/               # Page-level components (Dashboard, pm/, attendance/, bom/)
├── components/layout/   # AppLayout, Sidebar, Header
└── types/               # Shared TypeScript type definitions
```

The Vite dev server proxies `/api` → `http://localhost:8000`, so no CORS configuration is needed during development.

### Environment Variables

Stored in `backend/.env` (auto-generated by `./synapse prepare`):

| Variable | Default | Notes |
|----------|---------|-------|
| `DJANGO_SECRET_KEY` | auto-generated | Required |
| `DJANGO_DEBUG` | `True` (dev) | Set to `False` in prod |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost` | Comma-separated |
| `SYNAPSE_PM_BACKEND` | `database` | `vault` or `database` |
| `OBSIDIAN_VAULT_PATH` | — | Required if PM backend is `vault` |
| `ATTENDANCE_ANALYZER_RULE_URL` | — | Optional remote TOML rules URL |

### Development Roadmap

The project phase history and current status are documented in `docs/architecture/progress.md`.
The API contracts are in `docs/architecture/reference/api_spec.md`.
The codebase map (start here for AI agents) is `docs/architecture/reference/codebase_map.md`.

## Current Development Status

**Current Phase: 5.9 ✅ Complete → Next: Phase 5.8 (Plugin API)**

### Phase 5.9 — PostgreSQL + Docker Compose (COMPLETE)

All Phase 5.9 deliverables implemented:

- **`psycopg2-binary`** added to `requirements.txt`
- **`get_db_config()`** in `settings.py`: `DB_ENGINE` env var selects SQLite (dev default) or PostgreSQL (Docker/prod). Backward compatible — `./synapse run` unchanged.
- **`docker/Dockerfile`**: Python 3.12-slim + Gunicorn; `pip install -e backend/` for synapse_* importability
- **`docker/entrypoint.sh`**: pure-Python TCP probe waits for PostgreSQL → migrate → collectstatic → gunicorn
- **`docker/Dockerfile.nginx`**: multi-stage build (Node 20 builds Vue → Nginx Alpine serves static files)
- **`docker/nginx/nginx.conf`**: proxy to backend, static file serving, Vue SPA history-mode fallback
- **`docker-compose.yml`**: 3-service stack (postgres + backend + nginx); `static_volume` shared between backend (write) and nginx (read-only)
- **`.env.docker.example`**: template with all required/optional variables documented
- **`synapse docker:*`**: `docker:build/up/down/logs/shell` commands added to orchestrator
- **`db_adapter.py`**: PostgreSQL native JSONField `@>` operator for tag filtering (SQLite Python fallback kept)

### Phase 5.7 — Permission System + Multi-user (COMPLETE)

All Phase 5.7 deliverables are implemented and verified (build passes, `django check` 0 issues):

- **JWT auth**: `djangorestframework-simplejwt` installed. `POST /api/auth/login/` returns `{access, refresh, user}`. `POST /api/auth/refresh/` rotates tokens (7-day lifetime). `POST /api/auth/logout/` blacklists refresh token.
- **`synapse_auth` app**: New Django app at `backend/src/synapse_auth/`. `UserProfile` model (role + allowed_tags). Signal auto-creates profile on User save; superusers always get `role='admin'`.
- **User roles**: `admin` / `editor` / `viewer`. Custom permission classes: `IsAdminRole`, `IsEditorOrAbove` in `synapse_auth/permissions.py`.
- **User management API**: `GET/POST /api/auth/users/`, `GET/PATCH/DELETE /api/auth/users/{id}/` (admin only).
- **Tag-based access**: `_filter_projects_by_access()` in `synapse_pm/api/views.py`. Admins see all; editors/viewers see untagged projects + projects matching `allowed_tags`.
- **Frontend JWT client**: `api/client.ts` — JWT Bearer token, auto-refresh on 401, `synapse:session-expired` event on full expiry.
- **Auth store**: `stores/auth.ts` — `login()`, `logout()`, `fetchCurrentUser()→bool`, `isAdmin`/`isEditor` computed.
- **Custom login page**: `views/LoginView.vue` — Naive UI card, dark mode compatible, replaces Django admin redirect.
- **JWT router guard**: `router/index.ts` — redirects to `/login` (not `/admin/login/`), admin-only route guard.
- **Header**: username chip + role badge (red=admin, orange=editor, default=viewer) + logout button.
- **Sidebar**: "User Management" link visible only to admins.
- **UsersView**: `views/admin/UsersView.vue` — full CRUD table for admin.

### Next: Phase 5.8

- **5.8**: Plugin API framework (`SynapseModule` base class + MCP/AI agent interface)
