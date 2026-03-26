# SynapseERP — AI Agent Guide

> **Target audience:** AI coding agents (Claude Code, Cursor, etc.)
> **Read this before touching any code.**

---

## 1. Reading Order (every session)

1. **This file** — understand how to work in this repo
2. **[`reference/codebase_map.md`](reference/codebase_map.md)** — full codebase structure (replaces scanning, saves 50% time)
3. **[`progress.md`](progress.md)** — current Phase status and active tasks
4. **Relevant reference doc** — only if your task requires it (API spec, Obsidian rules, etc.)

---

## 2. Non-Negotiable Rules

### Code
- All source code and comments must be in **English**
- Communicate with the human in **Chinese**
- Do **not** end the session arbitrarily — always prompt the user for next steps

### Commits
- **One commit per STEP** — do not accumulate changes and commit at the end
- Follow the commit message format below exactly
- Never commit broken code or failing tests

### Documentation
- After modifying any file listed in `reference/codebase_map.md`, update that file in the same commit
- When a Phase step is completed, update the status in `progress.md`

---

## 3. Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Type** (required): `feat` · `fix` · `docs` · `refactor` · `perf` · `test` · `build` · `chore`

**Subject** (required): English, ≤70 chars, present tense, no leading capital
- ✅ `fix: handle null tags in project filtering`
- ❌ `Fixed bugs and updated stuff`

**Body** (recommended): bullet points explaining what and why

**Footer** (recommended): `Phase X.Y Step Z complete.`

---

## 4. How to Handle Human Requests

### "Build a new feature"
1. Ask clarifying questions (business goal, affected modules, API changes needed)
2. Write a Phase plan in `docs/architecture/` — **no code yet**
3. Wait for approval
4. Implement step by step, one commit per step

### "There's a bug"
1. Reproduce and understand the root cause
2. Fix it
3. Add the fix to the relevant section of `reference/codebase_map.md` under Known Issues
4. Commit with `fix:` prefix

### "Refactor / optimize something"
1. Write a refactor plan: `docs/architecture/REFACTOR_<NAME>.md`
2. Wait for approval
3. Execute step by step

---

## 5. Common Pitfalls

| ❌ Wrong | ✅ Right |
|---|---|
| Edit 10 files then do one big commit | Commit after each logical step |
| Start coding without reading codebase_map | Read codebase_map first |
| Edit code, forget to update codebase_map | Always sync codebase_map in same commit |
| Vague commit message "fix bugs" | Specific: "fix: null pointer in tag filter when project has no tags" |
| Skip tests "it should be fine" | Run `./synapse dev:test` before each commit |
| Invent new architectural patterns | Follow existing patterns in codebase_map |

---

## 6. Key Architecture Facts

- **DB-Primary**: The database is the single source of truth. Obsidian is an optional offline mirror.
- **JWT auth**: All API endpoints (except `/api/health/` and `/api/dashboard/`) require a Bearer token.
- **Three roles**: `admin` (full access) · `editor` (create/edit) · `viewer` (read-only)
- **Tag-based access**: editors/viewers only see projects whose tags match their `allowed_tags`
- **PM backend**: `SYNAPSE_PM_BACKEND` env var — always `database` in Docker, optionally `vault` in local dev
- **Version**: Defined in `backend/src/synapse/__init__.py`, exposed via `GET /api/health/`

---

## 7. Development Commands Reference

```bash
./synapse prepare          # First-time setup
./synapse run:all          # Backend (:8000) + frontend (:5173) + vault watcher
./synapse dev:test         # Run Django test suite
./synapse dev:migrate      # After changing models.py
./synapse docker:up        # Start Docker stack (postgres + backend + nginx)
./synapse docker:down      # Stop containers (data volumes preserved)
./synapse docker:clean     # ⚠️  Destroy everything including DB data
./synapse docker:manage createsuperuser   # Create admin user in Docker
```
