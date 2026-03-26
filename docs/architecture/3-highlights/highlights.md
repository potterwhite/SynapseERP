# SynapseERP — Technical Highlights

> What makes this project interesting and non-trivial.

---

## 1. DB-Primary + Obsidian-Mirror Architecture

Most Obsidian-integrated tools treat the vault as the source of truth. SynapseERP flips this:

- **Database is the single source of truth** — all writes go to PostgreSQL first
- **Obsidian is an optional offline client** — you can edit in Obsidian, and a sync service reconciles changes back to the DB
- **Conflict resolution**: last-modified-wins strategy based on file `mtime` vs DB `updated_at`
- **This means**: the app works fully without any Obsidian vault configured; the vault sync is additive

Key files: `backend/src/synapse_pm/vault/sync_service.py` · `backend/src/synapse_pm/vault/reader.py`

---

## 2. JWT Auth with Tag-Based Project Visibility

Beyond simple role-based access, the permission system supports **fine-grained tag filtering**:

- Each `UserProfile` has an `allowed_tags` JSONField (list of strings)
- `admin` role sees everything
- `editor` and `viewer` roles see: untagged projects + projects whose tags overlap with `allowed_tags`
- This is implemented in `_filter_projects_by_access()` using PostgreSQL native `@>` JSON containment operator (with a Python fallback for SQLite)

Use case: a manager can see the "personal" tag projects of their team without exposing other teams' work.

Key files: `backend/src/synapse_pm/api/views.py` · `backend/src/synapse_auth/` · `backend/src/synapse_pm/db_adapter.py`

---

## 3. Pluggable Backend Adapter Pattern

The PM module was originally designed with a `PMBackendAdapter` abstraction that allowed swapping between `DatabaseAdapter` and `VaultAdapter`. While the system now runs DB-Primary by default, the adapter pattern is preserved:

- `SYNAPSE_PM_BACKEND=database` (default) — uses `DatabaseAdapter`
- `SYNAPSE_PM_BACKEND=vault` — uses `VaultAdapter` (reads directly from Obsidian files)
- This leaves the door open for a future "read-only archive" mode or testing with fixture vaults

---

## 4. Obsidian Vault File Watcher (Auto-Sync)

The `VaultWatcher` class uses the `watchdog` library to monitor `.md` file changes in real time:

- Debounced by 5 seconds (configurable) to avoid flooding the DB on rapid edits
- Works across platforms: inotify (Linux), FSEvents (macOS), ReadDirectoryChangesW (Windows)
- Incremental import: only re-processes changed files, not the entire vault
- Exposed as a Django management command (`./synapse vault:watch`) and auto-started by `./synapse run:all` when a vault is configured

Key files: `backend/src/synapse_pm/vault/watcher.py` · `backend/src/synapse_pm/management/commands/vault_watch.py`

---

## 5. Docker Compose: One-Command Production-Like Stack

The Docker setup is designed to be genuinely useful, not just a demo:

- **Multi-stage Dockerfile.nginx**: Node builds the Vue SPA, then only the compiled `dist/` is copied into the Nginx image — zero Node.js runtime in production
- **Shared static volume**: Django `collectstatic` writes to a named volume; Nginx reads from the same volume read-only — no file copying between containers
- **TCP probe in pure Python**: `entrypoint.sh` waits for PostgreSQL to accept connections without requiring `pg_isready` or any extra tools in the image
- **Single-variable Obsidian mount**: setting `OBSIDIAN_VAULT_PATH` in `.env.docker` automatically bind-mounts the host directory at `/vault` inside the container (uses `${VAR:+/vault}` shell expansion)

Key files: `docker/Dockerfile` · `docker/Dockerfile.nginx` · `docker/entrypoint.sh` · `docker-compose.yml`

---

## 6. Dynamic Version from API

The frontend Header always shows the backend version dynamically:
- `GET /api/health/` returns `{"version": "0.9.0-alpha", ...}`
- `stores/app.ts` stores `appVersion` from this response
- `Header.vue` displays `appStore.appVersion` — no hardcoded string anywhere in the frontend

---

## 7. PARA Methodology Hidden Behind Generic PM UI

The vault uses the PARA structure (Projects, Areas, Resources, Archives) internally, but the UI exposes only generic PM concepts (projects, tasks, tags). Users don't need to know about PARA to use the system. This keeps the UI accessible while preserving the structured vault layout.

Reference: `docs/architecture/archived/05_para_mapping.md`
