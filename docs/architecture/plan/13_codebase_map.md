# SynapseERP — Codebase Map (AI Agent Quick Reference)

> **⚠️ FOR AI AGENTS — READ THIS FIRST**
> This document is the single source of truth for codebase structure.
> **Do NOT do a full repo scan** — read this file instead.
> It saves you hundreds of token-expensive file reads.
>
> **Maintenance rule:** Any AI agent that modifies a file listed here MUST update
> the relevant section in this document in the same commit/session.
>
> Last updated: 2026-03-26 (reflects Phase 5.6 complete state)

---

## 1. Repository Root Layout

```
SynapseERP.git/
├── backend/                   Django backend (Python 3.12)
│   ├── src/                   All Django apps live here
│   │   ├── synapse/           Core framework (version, shared utils)
│   │   ├── synapse_api/       health + dashboard + auth/me endpoints
│   │   ├── synapse_dashboard/ Notification model (markdown, shown on dashboard)
│   │   ├── synapse_attendance/ Excel attendance parser + TOML rules
│   │   ├── synapse_bom_analyzer/ Multi-file BOM aggregation
│   │   └── synapse_pm/        ⭐ Project Management (core module)
│   ├── synapse_project/       Django project config (settings, urls, wsgi)
│   ├── manage.py
│   ├── requirements.txt
│   └── .env                   (gitignored, auto-created by ./synapse prepare)
├── frontend/                  Vue 3 SPA (TypeScript + Vite 6)
│   ├── src/                   All frontend source
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   └── architecture/          ← YOU ARE HERE
├── synapse                    Unified CLI orchestrator (./synapse <cmd>)
├── docker/                    Docker configs (Phase 5.9, pending)
└── CLAUDE.md                  Instructions for Claude Code sessions
```

---

## 2. Backend — File-by-File Reference

### `backend/synapse_project/` (Django project config)

| File | Purpose |
|------|---------|
| `settings.py` | All settings. Reads from `.env`. Key: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `OBSIDIAN_VAULT_PATH`, `OBSIDIAN_SYNC_ENABLED`. DRF uses `SessionAuthentication` + `IsAuthenticated` by default. |
| `urls.py` | Root URL: mounts `/admin/`, `/api/`, `/i18n/` |
| `api_urls.py` | API root: includes `synapse_api.urls`, `synapse_pm.urls`, `synapse_attendance.api_urls`, `synapse_bom_analyzer.api_urls` |

### `backend/src/synapse_api/` (Core API)

| File | Purpose |
|------|---------|
| `urls.py` | `GET /api/health/`, `GET /api/dashboard/`, `GET /api/auth/me/` |
| `views.py` | `health_check` (AllowAny), `dashboard` (AllowAny), `current_user` (IsAuthenticated → returns `{id, username, email}`) |

### `backend/src/synapse_pm/` (PM Module — most complex)

```
synapse_pm/
├── models.py          Project, Task, TimeEntry, SyncMeta
├── serializers.py     ProjectSerializer, TaskSerializer, TimeEntrySerializer,
│                      GanttTaskSerializer, *WriteSerializer variants
├── urls.py            Delegates to api/urls.py
├── adapters/          BaseAdapter, DBAdapter (default), VaultAdapter
├── api/
│   ├── urls.py        All /api/pm/* URL patterns
│   └── views.py       All /api/pm/* view functions
└── vault/
    ├── reader.py      Parses Obsidian .md files
    ├── writer.py      Writes back to Obsidian .md files
    ├── sync_service.py ObsidianSyncService (import + export)
    └── watcher.py     VaultWatcher (watchdog-based auto-sync)
```

### `backend/src/synapse_pm/models.py` — Data Models

```python
# Project
Project:
  id, name, full_name, status('active'|'archived'|'on_hold'),
  para_type('project'|'archive'), vault_path, deadline(date),
  created(date), tags(JSONField list), vault_mtime(float), synced_at(datetime)

# Task
Task:
  uuid(UUID), name, project(FK→Project), status('todo'|'doing'|'done'|'cancelled'),
  priority('low'|'medium'|'high'), created(date), deadline(date),
  estimated_hours(float), depends_on(M2M→Task), vault_path, vault_mtime, synced_at

# TimeEntry
TimeEntry:
  task(FK→Task), date, description, start_time, end_time,
  duration_minutes(int), source_note_path

# SyncMeta (key-value store)
SyncMeta:
  key(unique str), value(text), updated_at
  # Common keys: "vault_path", "last_sync_at"
```

### `backend/requirements.txt` — Key Dependencies

```
Django>=5.0,<6.0
djangorestframework>=3.15
djangorestframework-simplejwt>=5.3   ← added in Phase 5.7
watchdog>=4.0
pandas>=2.2, numpy>=1.26.4, openpyxl
python-dotenv, PyYAML>=6.0
```

---

## 3. All REST API Endpoints

> Auth required = Django Session (Phase ≤5.6) → JWT Bearer (Phase 5.7+)

### Core (`/api/`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/health/` | None | Server health, version, PM backend mode |
| GET | `/api/dashboard/` | None | Latest notification (markdown) + module list |
| GET | `/api/auth/me/` | ✅ | Current user `{id, username, email}` |

### PM Projects (`/api/pm/`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/pm/projects/` | ✅ | List projects. Query: `status`, `search`, `ordering`, `tags`, `page`, `page_size` |
| POST | `/api/pm/projects/` | ✅ | Create project |
| GET | `/api/pm/projects/{id}/` | ✅ | Project detail + tasks list |
| PATCH | `/api/pm/projects/{id}/` | ✅ | Update project fields |
| DELETE | `/api/pm/projects/{id}/` | ✅ | Delete project |

### PM Tasks

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/pm/tasks/` | ✅ | List. Query: `project`, `status`, `priority`, `search`, `page` |
| POST | `/api/pm/tasks/` | ✅ | Create task |
| GET | `/api/pm/tasks/{uuid}/` | ✅ | Task detail |
| PATCH | `/api/pm/tasks/{uuid}/` | ✅ | Update task |
| DELETE | `/api/pm/tasks/{uuid}/` | ✅ | Soft-delete (sets status=cancelled) |

### PM Other

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/pm/time-entries/` | ✅ | List by `?task_uuid=` |
| POST | `/api/pm/time-entries/` | ✅ | Create time entry |
| GET | `/api/pm/stats/` | ✅ | Dashboard stats (totals) |
| GET | `/api/pm/gantt/` | ✅ | Gantt tasks, `?project={id}` |
| GET | `/api/pm/tags/` | ✅ | All distinct project tags |
| GET | `/api/pm/sync/` | ✅ | Vault sync status |
| POST | `/api/pm/sync/trigger/` | ✅ | Trigger import/export |
| GET/PATCH | `/api/pm/sync/config/` | ✅ | Vault path config |
| GET | `/api/pm/sync/watcher/` | ✅ | Watchdog availability |

### Auth (Phase 5.7 — NEW, to be added under `/api/auth/`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/login/` | None | JWT login → `{access, refresh}` |
| POST | `/api/auth/refresh/` | None | Refresh access token |
| POST | `/api/auth/logout/` | ✅ | Blacklist refresh token |
| GET | `/api/auth/me/` | ✅ | Current user + role |
| GET | `/api/auth/users/` | admin | List all users |
| POST | `/api/auth/users/` | admin | Create user |
| PATCH | `/api/auth/users/{id}/` | admin | Update user (role, allowed_tags) |
| DELETE | `/api/auth/users/{id}/` | admin | Delete user |

---

## 4. Frontend — File-by-File Reference

### `frontend/src/` Structure

```
frontend/src/
├── api/
│   ├── client.ts       Axios instance. baseURL='/api', withCredentials=true.
│   │                   Request interceptor: attaches X-CSRFToken from cookie.
│   │                   Response interceptor: normalises errors to Error(message).
│   └── pm.ts           All PM API call functions (pmApi.* wrappers)
├── stores/
│   ├── app.ts          Theme ('light'|'dark' → localStorage key 'synapse_theme'),
│   │                   sidebarCollapsed, pmBackend, vaultConnected, fetchHealth()
│   ├── auth.ts         user{id,username,email}, isAuthenticated, fetchCurrentUser(),
│   │                   clearAuth(). Phase 5.7: add role, JWT token management.
│   └── pm.ts           projects, tasks, stats, tags, meetingMode, syncing.
│                       createProject/updateProject/deleteProject,
│                       fetchTags, syncVault, visibleProjects (computed).
├── types/
│   ├── api.ts          PaginatedResponse<T>, ApiError
│   └── pm.ts           Project, Task, TimeEntry, PmStats interfaces
├── router/
│   └── index.ts        Routes + global guard. Guard calls GET /api/auth/me/;
│                       on 401 redirects to /admin/login/?next=/
│                       Phase 5.7: replace with JWT guard + /login route.
├── components/
│   └── layout/
│       ├── AppLayout.vue  NConfigProvider(theme) + NLayoutSider(desktop) +
│       │                  NDrawer(mobile). Mobile breakpoint: 768px.
│       ├── Header.vue     Logo, theme toggle (moon/sun), version label.
│       │                  Phase 5.7: add username + logout button.
│       └── Sidebar.vue    NMenu with routes: Dashboard, PM, Attendance, BOM.
│                          Phase 5.7: add Users link (admin only).
└── views/
    ├── Dashboard.vue       PM stats row + module cards + notification markdown
    ├── LoginView.vue       (Phase 5.7 — TO CREATE) Custom JWT login page
    ├── pm/
    │   ├── PmIndex.vue     Route switcher: ProjectList ↔ ProjectTaskView
    │   ├── ProjectList.vue Tag filter, meeting mode toggle, project table,
    │   │                   New/Edit/Delete via ProjectFormModal
    │   ├── ProjectTaskView.vue Task list for a project + TaskDetail drawer
    │   ├── GanttView.vue   frappe-gantt integration
    │   ├── TaskDetail.vue  Task detail side drawer
    │   ├── SyncSettings.vue Vault sync config + watcher info
    │   └── ProjectFormModal.vue Create/Edit project (name/status/deadline/tags)
    ├── attendance/
    │   └── Upload.vue      Excel upload → analyze → download
    ├── bom/
    │   └── Upload.vue      Multi-file BOM upload → summary → download
    └── admin/
        └── UsersView.vue   (Phase 5.7 — TO CREATE) User management (admin only)
```

### `frontend/vite.config.ts` — Dev Proxy

```typescript
// /api/* and /admin/* are proxied to http://localhost:8000 in dev.
// No CORS config needed. Same-origin in production (Nginx).
```

---

## 5. Authentication Flow

### Current (Phase ≤5.6): Django Session Auth

```
1. Browser loads SPA → router.beforeEach fires
2. GET /api/auth/me/ → 200 (session cookie present) → proceed
3.                   → 401/403 → redirect to /admin/login/?next=/
4. Django admin login sets session cookie
5. All API calls include session cookie (withCredentials: true)
6. Django CSRF: csrftoken cookie → X-CSRFToken header (unsafe methods)
```

### Phase 5.7: JWT Auth (replacing Session)

```
1. Browser loads SPA → router.beforeEach fires
2. Check localStorage for access token
3. GET /api/auth/me/ with Bearer token → 200 → proceed
4.                                      → 401 → try refresh token
5.   POST /api/auth/refresh/ → 200 → new access token → retry
6.                           → 401 → redirect to /login (custom Vue page)
7. /login page → POST /api/auth/login/ → {access, refresh} → store in localStorage
```

---

## 6. Settings & Environment Variables

File: `backend/.env` (auto-generated, gitignored)

| Variable | Default | Required |
|----------|---------|----------|
| `DJANGO_SECRET_KEY` | auto | ✅ |
| `DJANGO_DEBUG` | `True` | — |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost` | — |
| `CSRF_TRUSTED_ORIGINS` | `http://localhost:5173,...` | — |
| `OBSIDIAN_VAULT_PATH` | — | Only for vault sync |
| `OBSIDIAN_SYNC_ENABLED` | auto from vault path | — |
| `ATTENDANCE_ANALYZER_RULE_URL` | — | Optional |

### DRF Settings (in `settings.py`)

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        # Phase 5.7: add JWTAuthentication
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
}
```

---

## 7. Development Commands

```bash
./synapse prepare          # Full setup: venv + pip + migrate + npm install
./synapse run              # Django dev server :8000
./synapse frontend:run     # Vite dev server :5173
./synapse run:all          # Both in parallel
./synapse dev:migrate      # makemigrations + migrate
./synapse dev:test         # Django test suite
./synapse superuser        # Create superuser

# Single test
cd backend && ../.venv/bin/python manage.py test synapse_pm.tests.TestClass.test_method
```

---

## 8. Key Architectural Patterns

1. **DB-Primary + Obsidian-Mirror**: Database is always the source of truth. Obsidian vault is an optional mirror that syncs bidirectionally.

2. **PM Adapter Pattern**: All PM data access goes through `get_adapter()`. Returns `DBAdapter` (default) or `VaultAdapter` depending on env var. Views never touch models directly.

3. **Pinia Stores**: All async state lives in stores, not components. Components call store actions.

4. **Naive UI**: All UI components are from Naive UI. Always import from `naive-ui` directly (not auto-import plugin). Use `#trigger` slot for `NTooltip` (not `content` prop).

5. **Vue Router Guard**: Single global `beforeEach` guard. `sessionVerified` flag prevents repeated auth checks.

6. **Tag Filtering**: Python-side list comprehension (not SQL JSONField query) because SQLite lacks native JSON containment. Phase 5.9 (PostgreSQL) will fix this.
