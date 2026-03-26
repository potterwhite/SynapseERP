# SynapseERP — Documentation Index

> Last updated: 2026-03-26 · Branch: `feature/phase5-productization`

This is the top-level index. Every document in this directory is listed here.
Start here, then navigate to the section you need.

---

## Quick Navigation

| I want to… | Go to |
|---|---|
| **Understand the project as an AI Agent** | [`ai_agent_guide.md`](ai_agent_guide.md) |
| **See what makes this project interesting** | [`highlights.md`](highlights.md) |
| **Check current progress / roadmap** | [`progress.md`](progress.md) |
| **Read the full codebase map** | [`reference/codebase_map.md`](reference/codebase_map.md) |
| **Look up the REST API spec** | [`reference/api_spec.md`](reference/api_spec.md) |
| **Understand Obsidian parsing rules** | [`reference/obsidian_parsing_rules.md`](reference/obsidian_parsing_rules.md) |
| **See frontend config (Vite/Router/Pinia)** | [`reference/frontend_config.md`](reference/frontend_config.md) |
| **Read architecture decisions** | [`reference/tech_stack.md`](reference/tech_stack.md) · [`reference/architecture_vision.md`](reference/architecture_vision.md) |
| **Dig into historical decisions** | [`archived/`](archived/) |

---

## Directory Structure

```
docs/architecture/
├── 00_INDEX.md               ← You are here (top-level index only)
│
├── ai_agent_guide.md         How AI agents should work in this repo
├── highlights.md             Technical highlights and design decisions
├── progress.md               Current status + full Phase roadmap with step details
│
├── reference/                Detailed technical references (read while coding)
│   ├── codebase_map.md       ⭐ Full codebase map — read before scanning code
│   ├── api_spec.md           REST API request/response contracts
│   ├── obsidian_parsing_rules.md  VaultReader/Writer regex + path rules
│   ├── frontend_config.md    Vite / TypeScript / Router / Pinia config
│   ├── tech_stack.md         Confirmed tech stack and selection rationale
│   └── architecture_vision.md     Architecture philosophy and strategic positioning
│
├── archived/                 Historical documents — kept for context, no longer active
│   ├── 01_current_state_analysis.md
│   ├── 02_obsidian_integration_design.md
│   ├── 03_frontend_tech_decision.md
│   ├── 05_para_mapping.md
│   ├── 06_vue3_spa_architecture.md
│   ├── 07_vue_vs_python_clarification.md
│   ├── 09_implementation_plan.md
│   ├── 14_phase57_plan.md
│   └── 15_phase59_plan.md
│
└── NEED_TO_DO.md             Bug/task backlog (working notes)
```

---

## Current Status (one-line summary)

**Phase 5.9 ✅ complete.** Docker Compose stack running. Next: Phase 5.8 (Plugin API).
See [`progress.md`](progress.md) for the full picture.
