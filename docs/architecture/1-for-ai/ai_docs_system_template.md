# AI-First Documentation System — Portable Template

> **Purpose of this document:** Explain how to inject a structured, AI-optimised
> documentation system into any new project so that an AI coding agent (Claude Code,
> Cursor, Copilot, etc.) can orient itself instantly **without scanning source code**.
>
> This template is battle-tested in SynapseERP.  Copy the structure and adapt the
> content to your project.

---

## Why this system exists

When an AI agent starts a session it normally does one of two things:

| Without this system | With this system |
|---|---|
| Reads 50–200 source files to understand the project | Reads 2–3 doc files, then writes code |
| Spends 40–60% of its token budget just *understanding* the codebase | Spends >90% of tokens on the actual task |
| Invents architectural patterns that conflict with existing ones | Follows the project's own patterns |
| Forgets conventions across sessions | Re-reads the same doc every session in seconds |

The key insight: **the AI does not need to read code to understand structure —
it needs a well-maintained human-readable map**.

---

## The three-file core (minimum viable setup)

Every project needs at least these three files under `docs/`:

```
docs/
└── architecture/
    ├── 1-for-ai/
    │   ├── guide.md          ← Rules + commit format + architecture facts
    │   └── codebase_map.md   ← File-by-file reference (replaces source scanning)
    └── 2-progress/
        └── progress.md       ← Phase status + current active task
```

Plus an optional backlog file:
```
    └── 2-progress/
        └── NEED_TO_DO.md     ← Bug list / task backlog (checkbox format)
```

---

## File 1: `guide.md` — Working Rules for the AI Agent

This file is read **every session, first**.  It tells the agent:

1. **Non-negotiable rules** — language of code/comments, commit format, test policy
2. **How to handle different request types** — new feature / bug / refactor
3. **Common pitfalls** — what the agent tends to do wrong (very project-specific)
4. **Key architecture facts** — the 5–10 things the agent must never violate

### Template content

```markdown
# <ProjectName> — AI Agent Guide

## Non-Negotiable Rules

### Code
- All source code and comments must be in **English**
- Communicate with the human in **<preferred language>**
- Do NOT end the session — always prompt for next steps

### Commits
- One commit per logical step
- Format: `<type>: <subject>` (type: feat/fix/docs/refactor/test/chore)
- Never commit broken code

### Documentation
- After modifying any file listed in codebase_map.md, update that file in
  the same commit

## Key Architecture Facts
- <Fact 1: e.g. "DB is the single source of truth, not the file system">
- <Fact 2: e.g. "All API endpoints require Bearer JWT except /health/">
- <Fact 3: e.g. "Three roles: admin / editor / viewer — enforced server-side">
- ... (5–10 facts that matter most)

## How to Handle Requests

### "Build a new feature"
1. Ask clarifying questions
2. Write a plan in docs/ — no code yet
3. Wait for approval
4. Implement step by step

### "There's a bug"
1. Reproduce and understand root cause
2. Fix it
3. Commit with `fix:` prefix

## Common Pitfalls
| ❌ Wrong | ✅ Right |
|---|---|
| Edit 10 files then commit once | Commit after each logical step |
| Start coding without reading codebase_map | Always read codebase_map first |
| Skip codebase_map update | Always sync in same commit |
```

---

## File 2: `codebase_map.md` — The Most Important File

This replaces source-code scanning entirely.  A well-written codebase map lets the
agent jump straight to the right file without reading any source.

### What to include per file/module

```markdown
# <ProjectName> — Codebase Map

> ⚠️ FOR AI AGENTS — READ THIS BEFORE TOUCHING ANY CODE
> Last updated: <date>

## 1. Repository Layout (ASCII tree, top-level only)
<tree>

## 2. Backend — File-by-File Reference
### `src/<module>/models.py`
Brief: what models live here, their key fields and relationships.

### `src/<module>/views.py`
Brief: what endpoints/views live here, their auth requirements.

## 3. All REST API Endpoints (table format)
| Method | Path | Auth | Description |
...

## 4. Frontend — File-by-File Reference
### `src/stores/<name>.ts`
What state it manages, what actions it exposes.

### `src/views/<Name>.vue`
What it renders, what store it depends on.

## 5. Key Architectural Patterns (numbered list)
1. Pattern name — 1-2 sentence explanation
2. ...
```

### Maintenance rule

**Every AI agent that modifies a file listed in `codebase_map.md` MUST update the
relevant section in the same commit.**  This is enforced by placing the rule in
both `CLAUDE.md` and `guide.md`.

---

## File 3: `progress.md` — Current Phase Status

Gives the agent context on *where* the project is, so it doesn't propose already-done
features or contradict completed architecture decisions.

```markdown
# <ProjectName> — Progress

## Overall Status
| Phase | Description | Status |
|---|---|---|
| 1 | <description> | ✅ Done |
| 2 | <description> | 🔄 In Progress |
| 3 | <description> | ⏳ Pending |

**Currently active:** Phase 2.3 — <active step name>

## Phase 1 — <Name>
| Step | Description | Commit |
|---|---|---|
| 1.1 | <what was done> | `abc1234` |
...
```

---

## Entry point: `CLAUDE.md` at repo root

This is the **session start hook** — Claude Code reads `CLAUDE.md` automatically
on every session start.

```markdown
# CLAUDE.md

## ⚠️ Session Start Protocol

Before writing any code, read in order:
1. `docs/architecture/1-for-ai/guide.md`
2. `docs/architecture/1-for-ai/codebase_map.md`

Then check `docs/architecture/2-progress/progress.md` for current phase status.

Do NOT scan `src/` before reading the above.

## Requirements
- All source code and comments in **English**
- Communicate in **<human's language>**
- Never end the session without prompting for next steps

## Commands
<your project's key CLI commands>
```

### Why CLAUDE.md must be short

`CLAUDE.md` is injected into every prompt.  Keep it under 60 lines.  All detail
goes in the doc files it points to — those are read once per session, not every
turn.

---

## Optional: `NEED_TO_DO.md` — Living Backlog

A plain Markdown checkbox list.  The agent reads it, does the unchecked items,
and checks them off.  Simple, no tooling needed.

```markdown
# Backlog

Mar 26 2026
- [x] Fix export-to-vault permission error
- [x] Add batch delete for projects and tasks
- [ ] Complete i18n for all frontend strings
- [ ] Write AI docs system template for other projects
```

**Convention:** Group by date.  Newest at the top.  Checked = done.

---

## Full directory structure (SynapseERP example, for reference)

```
docs/
└── architecture/
    ├── 1-for-ai/                       ← AI agent reads these
    │   ├── guide.md                    ← Session rules + commit format
    │   ├── codebase_map.md             ← File-by-file reference map
    │   ├── api_spec.md                 ← Full REST API reference
    │   ├── obsidian_parsing_rules.md   ← Domain-specific rules
    │   ├── frontend_config.md          ← Frontend build / env details
    │   └── ai_docs_system_template.md  ← THIS FILE
    ├── 2-progress/                     ← Project tracking
    │   ├── progress.md                 ← Phase status + roadmap
    │   └── NEED_TO_DO.md              ← Active bug/task backlog
    └── 3-highlights/                   ← Technical showcases
        └── architecture_vision.md      ← Key design decisions + vision
```

The `3-highlights/` directory is optional — use it for architectural decision
records (ADRs) or showcasing interesting technical choices for new team members.

---

## Injecting this system into a new project — checklist

```
[ ] Create docs/architecture/1-for-ai/guide.md
    - Fill in project-specific rules, pitfalls, and architecture facts
[ ] Create docs/architecture/1-for-ai/codebase_map.md
    - Map every important file with a 1-2 sentence description
    - Add the "Last updated: <date>" header — agents use this to judge freshness
[ ] Create docs/architecture/2-progress/progress.md
    - List completed and in-progress phases
[ ] Create CLAUDE.md at repo root
    - Session start protocol: point to the three files above
    - Keep it under 60 lines
[ ] Add maintenance rule to both CLAUDE.md and guide.md:
    "Any agent that modifies a file in codebase_map must update codebase_map
     in the same commit."
[ ] (Optional) Create docs/architecture/2-progress/NEED_TO_DO.md
    for active bug/task backlog
```

---

## What makes a good codebase map entry

**Bad** (too vague, forces the agent to open the file anyway):
```
### `src/api/views.py`
Contains API views.
```

**Good** (enough detail to act without opening the file):
```
### `src/synapse_pm/api/views.py`
All /api/pm/* view functions.
- project_list: GET (filter: status, search, tags, page) + POST
- project_detail: GET/PATCH/DELETE by id
- task_list: GET (filter: project, status, priority, search) + POST
- gantt_tasks: GET /api/pm/gantt/ — returns GanttTask-serialized tasks
- tag_list: GET /api/pm/tags/ — all distinct project tags
Access control: _filter_projects_by_access() applies role + allowed_tags filter
```

---

## Summary

| File | Frequency of reads | Purpose |
|---|---|---|
| `CLAUDE.md` | Every turn (auto-injected) | Session entry point — minimal |
| `guide.md` | Once per session | Rules + facts |
| `codebase_map.md` | Once per session | Structure + file reference |
| `progress.md` | Once per session | Current phase context |
| `NEED_TO_DO.md` | When working on bugs | Active backlog |
| Domain docs (`api_spec.md`, etc.) | Only when needed | Deep reference |

The system costs ~2,000–4,000 tokens per session on startup reads.
It saves 20,000–80,000 tokens by eliminating source-code scanning.
ROI is positive after the very first task.
