# SynapseERP — Project Progress

> Last updated: 2026-03-26

---

## Overall Status

| Phase | Description | Status |
|---|---|---|
| **Phase 0** | Project restructure + infrastructure | ✅ Done |
| **Phase 1** | Vue 3 frontend skeleton + API foundation | ✅ Done |
| **Phase 2** | PM core — Obsidian read + display | ✅ Done |
| **Phase 3** | PM advanced — Gantt + write-back | ✅ Done |
| **Phase 4** | Migrate existing modules to Vue | ✅ Done |
| **Phase 4.5** | End-to-end integration testing | ✅ Done |
| **Phase 5** | Productization — auth, multi-user, sync, UI | 🔄 In Progress |
| **Phase 6** | Continuous extension (Plugin API, AI integration) | ⏳ Pending |

**Currently active:** Phase 5.8 (Plugin API framework) — not yet started.

---

## Phase 0 — Project Restructure + Infrastructure

| Step | Description | Commit |
|---|---|---|
| **0.1** | Create `backend/` dir, migrate Django code | `0b29271` |
| **0.2** | Install DRF, API foundation + health check | `536693f` |
| **0.3** | Initialize Vue 3 + Vite + TypeScript project | `a25c6ed` |
| **0.4** | Configure Obsidian vault path | `5cd2a0e` |

---

## Phase 1 — Vue 3 Frontend Skeleton

| Step | Description | Commit |
|---|---|---|
| **1.1** | AppLayout + Sidebar + Vue Router | `3b37d43` |
| **1.2** | Pinia stores + Axios API client | `2cc0a2a` |
| **1.3** | Migrate Dashboard page to Vue | `6770c35` |

---

## Phase 2 — PM Core (Obsidian Read + Display)

| Step | Description | Commit |
|---|---|---|
| **2.1** | Create `synapse_pm` Django app + DB models | `3d9f20e` |
| **2.2** | `PMBackendAdapter` abstract layer | `de6ca5e` |
| **2.3** | `VaultReader` + `VaultWriter` | `8434066` |
| **2.4** | Vault-to-SQLite cache sync | `3cf45e9` |
| **2.5** | DRF REST API — PM endpoints | `22c3fe7` |
| **2.6** | Vue frontend — ProjectList + TaskDetail views | `2c45168` |

---

## Phase 3 — PM Advanced (Gantt + Write-back)

| Step | Description | Commit |
|---|---|---|
| **3.1** | Integrate frappe-gantt chart | `1ebc3e8` |
| **3.2** | Gantt drag-and-drop interactions | `1ebc3e8` |
| **3.3** | VaultWriter write-back to Obsidian | *(implemented in 2.3)* |
| **3.4** | Write API endpoints | *(implemented in 2.5)* |

---

## Phase 4 — Migrate Existing Modules to Vue

| Step | Description | Commit |
|---|---|---|
| **4.1** | Attendance Analyzer DRF API + Vue views | `b906072` |
| **4.2** | BOM Analyzer DRF API + Vue views | `b906072` |
| **4.3** | Remove all Django template routes | `19f483c` |

---

## Phase 4.5 — End-to-End Integration Testing

| Check | Result | Notes |
|---|---|---|
| Auth flow: unauthenticated → login → SPA | ✅ Pass | |
| Backend API health (health / dashboard / pm/*) | ✅ Pass | |
| PM: project list / task view / Gantt / TaskDetail | ✅ Pass | |
| Attendance Analyzer: upload → analyze → download | ✅ Pass | ⚠️ zh download showed English headers (fixed in 5.1) |
| BOM Analyzer: multi-file upload → aggregate → download | ✅ Pass | |
| Gantt drag: modify deadline → PATCH → refresh | ✅ Pass | ⚠️ UX improved in 5.1 |

---

## Phase 5 — Productization

> **Architectural decision (2026-03-25):** Phase 5 switched to **DB-Primary + Obsidian-Mirror**.
> Database is the single source of truth; Obsidian is the admin's "offline client".

### Phase 5.1 — Bug Fixes ✅

| Item | Status |
|---|---|
| Attendance zh-Hans download shows English headers | ✅ Fixed |
| Gantt drag UX (real drag instead of cell-by-cell + instant popup) | ✅ Fixed |
| Admin login page styling | ✅ Fixed |

### Phase 5.2 — DB-Primary Architecture Cleanup ✅

| Item | Status |
|---|---|
| Remove vault/database toggle switch | ✅ Done |
| API always uses DatabaseAdapter | ✅ Done |
| Add missing Project CRUD endpoints | ✅ Done |

### Phase 5.3 — Obsidian Sync Service ✅

| Item | Status |
|---|---|
| Standalone `ObsidianSyncService` (import + export) | ✅ Done |
| Dynamic vault path config (Admin UI + API) | ✅ Done |
| Conflict strategy: last-modified-wins | ✅ Done |
| Frontend SyncSettings view | ✅ Done |
| Bug fix: duplicate projects on vault path change | ✅ Fixed — use `full_name` as stable key |

### Phase 5.4 — Tag Filtering + Project Visibility ✅

| Item | Status |
|---|---|
| `tags` JSONField on Project model | ✅ Done |
| Tag filter UI (multi-select dropdown) | ✅ Done |
| Meeting mode: one-click hide personal-tagged projects | ✅ Done |
| `GET /api/pm/tags/` returns all distinct tags | ✅ Done |

### Phase 5.5 — Vault Auto-Sync ✅

| Item | Status |
|---|---|
| `watchdog>=4.0` added to requirements.txt | ✅ Done |
| `VaultWatcher` class (5s debounce, cross-platform) | ✅ Done |
| `vault_watch` Django management command (`--debounce`, `--once`) | ✅ Done |
| `./synapse vault:watch [SEC]` orchestrator alias | ✅ Done |
| `GET /api/pm/sync/watcher/` returns watchdog availability | ✅ Done |
| Frontend: Auto-Sync card in SyncSettings | ✅ Done |
| **Constraint documented:** task files must live in `<project_dir>/tasks/*.md` with `task_uuid` in frontmatter | ✅ Documented |

### Phase 5.6 — UI/UX Overhaul ✅

| Item | Status |
|---|---|
| Dashboard redesign (modern card layout) | ✅ Done |
| Responsive layout (mobile/tablet breakpoints) | ✅ Done |
| Dark mode + theme persistence (localStorage) | ✅ Done |
| Frontend Project CRUD modal (create / edit / delete) | ✅ Done |
| Bug fix: `NTooltip` trigger slot crash → white screen | ✅ Fixed |

### Phase 5.7 — Permission System + Multi-user ✅

| Item | Status |
|---|---|
| JWT auth via `djangorestframework-simplejwt` | ✅ Done |
| `synapse_auth` app: `UserProfile` model (role + allowed_tags) | ✅ Done |
| Three roles: `admin` / `editor` / `viewer` | ✅ Done |
| Tag-based project access control (`_filter_projects_by_access()`) | ✅ Done |
| Custom login page (`LoginView.vue`) | ✅ Done |
| JWT router guard (redirects unauthenticated to `/login`) | ✅ Done |
| Header: username chip + role badge + logout button | ✅ Done |
| Sidebar: "User Management" visible to admins only | ✅ Done |
| Admin UsersView: full CRUD table | ✅ Done |
| Self-registration (`POST /api/auth/register/` + `RegisterView.vue`) | ✅ Done |

### Phase 5.8 — Plugin API Framework ⏳ Not started

| Item | Status |
|---|---|
| `SynapseModule` base class + standard interface | ⏳ |
| Each module registers available actions | ⏳ |
| Reserve interface for AI Agents (MCP / OpenClaw) | ⏳ |

### Phase 5.9 — PostgreSQL Migration + Docker Compose ✅

| Item | Status |
|---|---|
| `psycopg2-binary` in requirements.txt | ✅ Done |
| `get_db_config()` in settings.py: `DB_ENGINE` selects SQLite or PostgreSQL | ✅ Done |
| `docker/Dockerfile`: Python 3.12-slim + Gunicorn | ✅ Done |
| `docker/entrypoint.sh`: pure-Python TCP probe → migrate → collectstatic → gunicorn | ✅ Done |
| `docker/Dockerfile.nginx`: multi-stage (Node builds Vue → Nginx serves dist) | ✅ Done |
| `docker/nginx/nginx.conf`: proxy + static files + Vue SPA history-mode fallback | ✅ Done |
| `docker-compose.yml`: 3-service stack (postgres + backend + nginx) | ✅ Done |
| `.env.docker.example`: template with all variables documented | ✅ Done |
| `synapse docker:*` commands: build/up/down/clean/logs/shell/manage | ✅ Done |
| `db_adapter.py`: PostgreSQL native `@>` operator for tag filtering | ✅ Done |
| Single-variable Obsidian vault mount (`OBSIDIAN_VAULT_PATH:+/vault`) | ✅ Done |

---

## Phase 5 — Original Requirements Traceability

| Original requirement | Mapped to | Notes |
|---|---|---|
| #1 Tag-based show/hide of personal projects | 5.4 | tags + meeting mode |
| #2 Vault auto-sync | 5.5 | watchdog file watcher, no polling |
| #3 UI too ugly | 5.6 | Dashboard redesign + responsive |
| #4 Low resource usage, mobile-friendly | 5.5 + 5.6 | event-based watcher + responsive layout |
| #5 OpenClaw / AI integration | 5.8 | Reserve Plugin API — no AI code yet |
| #6 Docker Compose | 5.9 | 3-service stack |
| #7 Dynamic vault path config | 5.3 | Merged into sync service |
| #8 Value proposition + multi-user | 5.7 + architecture_vision | Permission system + vision doc |
| 🆕 DB-Primary architecture cleanup | 5.2 | Remove toggle switch, complete CRUD |
| 🆕 Obsidian sync service | 5.3 | Standalone bidirectional sync |
| 🆕 PostgreSQL migration | 5.9 | SQLite JSON query limits → PostgreSQL |

---

## Phase 6 — Future Extensions (Pending)

These are not scheduled yet. Listed here for reference.

- **Plugin API** (5.8 completes the foundation): external tools can register as SynapseModules
- **MCP / AI Agent interface**: AI agents query and mutate ERP data via the Plugin API
- **Kubernetes deployment**: Helm chart for cloud-native hosting
- **Mobile app**: React Native or Flutter client consuming the same REST API
- **More modules**: CRM, Inventory, Finance (each as a pluggable Django app)
