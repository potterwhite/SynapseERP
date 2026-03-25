# Changelog

---

## [0.9.0](https://github.com/potterwhite/SynapseERP/compare/v0.8.7...v0.9.0) (2026-03-25)


### ✨ Added

* complete PM module, Vue SPA migration, and Obsidian vault integration ([ac55b1c](https://github.com/potterwhite/SynapseERP/commit/ac55b1caa255b7d3602fb29c97d166c242fb1607))
* **PM module** — full project management app with `Project`, `Task`, `TimeEntry` models and dual backend (database / Obsidian vault)
* **Vault integration** — VaultReader/VaultWriter for Obsidian vault parsing and real-time write-back
* **Task UI** — "New Task" modal and "Edit Task" drawer with vault write-back support
* **Gantt chart** — frappe-gantt integration with drag-and-drop deadline updates
* **Vue SPA** — full frontend migration (Dashboard, PM, Attendance, BOM) on Vue 3 + Naive UI
* **REST API** — DRF endpoints for projects, tasks, time entries, stats, and vault sync

### 🐛 Fixed

* Layout width capped at 1126px — removed Vite scaffold CSS cap
* Sidebar not filling browser height on expand — added `height: 100%`
* New tasks landing in root `tasks/` instead of project subfolder — resolved `project_ref`
* Task identification via filename prefix — switched to `task_uuid` frontmatter
* Session cookie not forwarded through Vite dev proxy
* `release-please-config.json` wrong `package-name` (`ArcForge` → `SynapseERP`)

### ♻️ Refactored

* Removed all Django template routes; Vue SPA served via Nginx in production

### 📚 Documentation

* README overhaul (EN + ZH) with version badge, Python 3.10+, Django 5.x badges
* Moved `assets/` to `docs/assets/`; updated all image references
* Added MIT license headers to all source files
* Bootstrapped release-please configuration

---
