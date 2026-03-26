# SynapseERP — Codebase Map (AI Agent Quick Reference)

> **⚠️ FOR AI AGENTS — READ THIS FIRST**
> This document is the single source of truth for codebase structure.
> **Do NOT do a full repo scan** — read this file instead.
> It saves you hundreds of token-expensive file reads.
>
> **Maintenance rule:** Any AI agent that modifies a file listed here MUST update
> the relevant section in this document in the same commit/session.
>
> Last updated: 2026-03-26 (reflects Phase 5.7 complete state)

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
| `settings.py` | All settings. Reads from `.env`. Key: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `OBSIDIAN_VAULT_PATH`, `OBSIDIAN_SYNC_ENABLED`. DRF uses `JWTAuthentication` (primary) + `SessionAuthentication` (for /admin/). `SIMPLE_JWT` config: 60min access, 7day refresh, rotate. |
| `urls.py` | Root URL: mounts `/admin/`, `/api/`, `/i18n/` |
| `api_urls.py` | API root: includes `synapse_auth.urls` (first), `synapse_api.urls`, `synapse_pm.urls`, `synapse_attendance.api_urls`, `synapse_bom_analyzer.api_urls` |

### `backend/src/synapse_auth/` (JWT Auth + User Management — Phase 5.7)

```
synapse_auth/
├── __init__.py
├── apps.py         AppConfig — loads signals on ready()
├── models.py       UserProfile (OneToOne→User, role, allowed_tags)
├── signals.py      post_save signal: auto-creates UserProfile; superuser→admin role
├── serializers.py  UserSerializer, UserCreateSerializer, UserUpdateSerializer
├── views.py        login_view, logout_view, CustomTokenRefreshView, current_user,
│                   user_list, user_detail
├── urls.py         /auth/login/, /auth/logout/, /auth/refresh/, /auth/me/,
│                   /auth/users/, /auth/users/{id}/
└── permissions.py  IsAdminRole, IsEditorOrAbove
```

**UserProfile model:**
```python
UserProfile:
  user: OneToOneField(User)
  role: 'admin' | 'editor' | 'viewer'  (default: 'viewer')
  allowed_tags: JSONField[list[str]]    (default: [])
  created_at: DateTimeField
  # Methods: effective_role (superuser always→admin), can_see_project(tags)
```

### `backend/src/synapse_api/` (Core API)

| File | Purpose |
|------|---------|
| `urls.py` | `GET /api/health/`, `GET /api/dashboard/`. Note: `auth/me/` was moved to `synapse_auth` in Phase 5.7. |
| `views.py` | `health_check` (AllowAny), `dashboard` (AllowAny). `current_user` removed (now in `synapse_auth`). |

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
| POST | `/api/auth/login/` | None | JWT login → `{access, refresh, user}` |
| POST | `/api/auth/refresh/` | None | Refresh access token (rotates refresh too) |
| POST | `/api/auth/logout/` | ✅ | Blacklist refresh token |
| GET | `/api/auth/me/` | ✅ | Current user `{id, username, email, role, allowed_tags}` |
| GET | `/api/auth/users/` | admin | List all users |
| POST | `/api/auth/users/` | admin | Create user |
| GET/PATCH/DELETE | `/api/auth/users/{id}/` | admin | User detail / update role+tags / delete |

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
│   │                   Request interceptor: attaches JWT Bearer token from localStorage.
│   │                   Response interceptor: on 401 auto-refresh, then retry.
│   │                   On refresh failure: fires 'synapse:session-expired' custom event.
│   │                   Exports: ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY constants.
│   ├── auth.ts         Auth API calls: authApi.login/logout/me, userApi.list/get/create/update/delete
│   └── pm.ts           All PM API call functions (pmApi.* wrappers)
├── stores/
│   ├── app.ts          Theme ('light'|'dark' → localStorage key 'synapse_theme'),
│   │                   sidebarCollapsed, pmBackend, vaultConnected, fetchHealth()
│   ├── auth.ts         user{id,username,email,role,allowed_tags,is_superuser},
│   │                   isAuthenticated, isAdmin(computed), isEditor(computed).
│   │                   login(u,p), logout(), fetchCurrentUser()→bool, clearAuth().
│   │                   Listens for 'synapse:session-expired' to clear state.
│   └── pm.ts           projects, tasks, stats, tags, meetingMode, syncing.
│                       createProject/updateProject/deleteProject,
│                       fetchTags, syncVault, visibleProjects (computed).
├── types/
│   ├── api.ts          PaginatedResponse<T>, ApiError
│   ├── auth.ts         User, UserRole types (Phase 5.7)
│   └── pm.ts           Project, Task, TimeEntry, PmStats interfaces
├── router/
│   └── index.ts        Routes + JWT guard. Public routes: /login (meta.public=true).
│                       Guard: checks isAuthenticated, calls fetchCurrentUser() once.
│                       On fail: redirect to /login?redirect=<path> (NOT /admin/login/).
│                       Admin guard: meta.requiresAdmin=true → non-admins → /dashboard.
├── components/
│   └── layout/
│       ├── AppLayout.vue  NConfigProvider(theme) + NLayoutSider(desktop) +
│       │                  NDrawer(mobile). Mobile breakpoint: 768px.
│       ├── Header.vue     Logo, theme toggle, user info (username + role badge),
│       │                  logout button. Role badge: admin=red, editor=orange, viewer=default.
│       └── Sidebar.vue    NMenu. "User Management" item visible only when authStore.isAdmin.
└── views/
    ├── LoginView.vue       ⭐ Custom JWT login page (Phase 5.7). Naive UI card, dark mode.
    ├── Dashboard.vue       PM stats row + module cards + notification markdown
    ├── pm/                 (unchanged from Phase 5.6)
    │   ├── PmIndex.vue     Route switcher: ProjectList ↔ ProjectTaskView
    │   ├── ProjectList.vue Tag filter, meeting mode toggle, project table, CRUD modal
    │   ├── ProjectTaskView.vue Task list for a project + TaskDetail drawer
    │   ├── GanttView.vue   frappe-gantt integration
    │   ├── TaskDetail.vue  Task detail side drawer
    │   ├── SyncSettings.vue Vault sync config + watcher info
    │   └── ProjectFormModal.vue Create/Edit project (name/status/deadline/tags)
    ├── admin/
    │   └── UsersView.vue   ⭐ User management CRUD (Phase 5.7, admin only)
    ├── attendance/
    │   └── Upload.vue      Excel upload → analyze → download
    └── bom/
        └── Upload.vue      Multi-file BOM upload → summary → download
```

### `frontend/vite.config.ts` — Dev Proxy

```typescript
// /api/* and /admin/* are proxied to http://localhost:8000 in dev.
// No CORS config needed. Same-origin in production (Nginx).
```

---

## 5. Authentication Flow (Phase 5.7 — JWT)

```
1. Browser loads SPA → router.beforeEach fires
2. authChecked=false: call authStore.fetchCurrentUser()
   └─ Reads localStorage 'synapse_access_token'
   └─ GET /api/auth/me/ with Bearer token
      → 200: user + role loaded, proceed
      → 401: Axios interceptor fires refresh attempt
             POST /api/auth/refresh/ → new access token → retry
             Still 401: clear tokens, fire 'synapse:session-expired'
3. isAuthenticated=false → redirect { name: 'login', query: { redirect: to.fullPath } }
4. /login page: POST /api/auth/login/ → { access, refresh, user }
   → store tokens in localStorage → router.push(redirect || '/')

Token storage keys:
  'synapse_access_token'  — 60min, JWT Bearer
  'synapse_refresh_token' — 7 days, rotated on each refresh call

Role-based access:
  admin  → sees ALL projects, can access /admin/users
  editor → sees untagged projects + projects matching allowed_tags
  viewer → same visibility as editor but read-only (write ops rejected by IsEditorOrAbove)
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
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # primary (Phase 5.7)
        'rest_framework.authentication.SessionAuthentication',          # kept for /admin/
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
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

5. **JWT Auth Guard**: Single global `beforeEach` guard. `authChecked` flag prevents repeated `fetchCurrentUser()` calls. Failed 401 → `/login` (not `/admin/login/`). Axios interceptor auto-refreshes tokens on 401.

6. **Tag Filtering (PM)**: Python-side list comprehension (`_filter_projects_by_access()` in `synapse_pm/api/views.py`) filters projects by user role + allowed_tags. Admin sees all. Phase 5.9 (PostgreSQL) will enable native SQL JSON containment queries.
