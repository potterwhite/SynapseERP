# CLAUDE.md

This file provides essential guidance to Claude Code when working in this repository.
**For full context, always start by reading the docs** (see below).

## ⚠️ Session Start Protocol

**Before writing any code**, read these two files in order:

1. `docs/architecture/1-for-ai/guide.md` — working rules, commit format, key architecture facts
2. `docs/architecture/1-for-ai/codebase_map.md` — full codebase map (do NOT scan files instead)

Then check `docs/architecture/2-progress/progress.md` for current phase status.

Do **not** scan `backend/src/` or `frontend/src/` before reading the above.

---

## Requirements

- All source code and comments must be in **English**
- Communicate with me in **Chinese**
- Do not end the session arbitrarily — always prompt the user for next steps

---

## Commands

All operations go through `./synapse` at the repo root.

### Local Development
```bash
./synapse prepare          # First-time setup (venv, pip, migrate, npm)
./synapse run:all          # Backend (:8000) + frontend (:5173) + vault watcher
./synapse run              # Backend only
./synapse frontend:run     # Frontend only
./synapse superuser        # Create Django admin superuser
./synapse dev:migrate      # makemigrations + migrate (after models.py changes)
./synapse dev:test         # Run Django test suite
./synapse clean            # ⚠️  Destructive: remove .venv, DB, node_modules
```

### Docker
```bash
cp .env.docker.example .env.docker   # First-time: fill in SECRET_KEY + DB_PASSWORD
./synapse docker:up              # Build + start all services
./synapse docker:down            # Stop containers (volumes preserved)
./synapse docker:clean           # ⚠️  Destroy containers + volumes + images (data loss!)
./synapse docker:logs [service]  # Tail logs
./synapse docker:shell           # Shell in backend container
./synapse docker:manage createsuperuser  # Create admin user
```

### Single test
```bash
cd backend && ../.venv/bin/python manage.py test synapse_pm.tests.TestClass.test_method
```

---

## Documentation Map

| Need | File |
|---|---|
| Working rules + commit format | `docs/architecture/1-for-ai/guide.md` |
| Codebase structure | `docs/architecture/1-for-ai/codebase_map.md` |
| REST API spec | `docs/architecture/1-for-ai/api_spec.md` |
| Obsidian parsing rules | `docs/architecture/1-for-ai/obsidian_parsing_rules.md` |
| Phase progress + roadmap | `docs/architecture/2-progress/progress.md` |
| Active task backlog | `docs/architecture/2-progress/NEED_TO_DO.md` |
| Architecture vision | `docs/architecture/3-highlights/architecture_vision.md` |
