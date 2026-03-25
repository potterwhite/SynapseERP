# Squash Merge Guide — PR #1 → main

## 1. Squash Commit Message

复制下面整段（包含空行）作为 squash commit 的 message。

> **格式说明 / Format notes:**
> - Title 行使用 `feat:` 不带 scope 括号，确保 release-please 正确识别 minor bump
> - Body 按 Added / Fixed / Refactored / Docs 分类，每项用动词开头
> - 符合 [Conventional Commits 1.0.0](https://www.conventionalcommits.org/) 规范

```
feat: complete PM module, Vue SPA migration, and Obsidian vault integration

Added:
- Project Management app (synapse_pm) with Project, Task, TimeEntry models
- Backend Adapter pattern — switchable between database and Obsidian vault
- VaultReader/VaultWriter for Obsidian vault parsing and write-back
- Vault-to-SQLite incremental sync via mtime tracking (sync_vault command)
- DRF REST API for projects, tasks, time entries, stats, and Gantt data
- Vue PM frontend — ProjectList, ProjectTaskView, GanttView, TaskDetail drawer
- frappe-gantt chart integration with drag-and-drop deadline updates
- Create/Edit task UI with vault write-back support
- Attendance Analyzer and BOM Analyzer migrated to Vue SPA with DRF APIs
- Vue 3 + TypeScript + Vite project skeleton with Naive UI
- App layout shell — sidebar navigation, header, responsive container
- Pinia state management + Axios API client with auth interceptors
- Dashboard page — Markdown notification display + module toolbox cards
- DRF API infrastructure with health check endpoint
- Obsidian vault path and PM backend mode configuration

Fixed:
- Layout width capped at 1126px by Vite scaffold CSS — removed cap
- Sidebar not filling browser height on expand — added height: 100%
- New tasks created in root tasks/ instead of project subfolder — resolved project_ref
- Task identification relied on filename prefix — switched to frontmatter task_uuid
- Session cookie not forwarded through Vite dev proxy
- release-please config had wrong package-name (ArcForge → SynapseERP)
- Pre-launch debug fixes — API response shape, auth guard, deployment config

Refactored:
- Removed all Django template routes; Vue SPA served via Nginx in production

Docs:
- README overhaul (EN + ZH) with auto-detected version badge
- Moved assets/ to docs/assets/, updated all image references
- Added MIT license headers to all source files
- Bootstrapped release-please configuration
```

---

## 2. CHANGELOG Entry（粘贴到 CHANGELOG.md 最顶部，release-please 会在下次自动维护）

```markdown
## [0.9.0](https://github.com/potterwhite/SynapseERP/compare/v0.8.7...v0.9.0) (2026-03-25)

### ✨ Added

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
```

---

## 3. 操作步骤

1. 打开 https://github.com/potterwhite/SynapseERP/pull/1
2. 点 **"Squash and merge"** 下拉按钮
3. **Title 行**：粘贴 Section 1 的第一行 `feat: complete PM module, Vue SPA migration, and Obsidian vault integration`
4. **Body 框**：粘贴 Section 1 中 `Added:` 到 `Bootstrapped release-please configuration` 的全部内容
5. 点确认 merge
6. release-please 会在 main 上自动触发，生成一个 "chore(release): v0.9.0" 的 PR
7. 审批并 merge 那个 release PR，即可自动打 tag `v0.9.0` 并生成 GitHub Release

> **⚠️ 关键：** Title 使用 `feat:` 不带括号，这样 release-please 能正确识别为 minor version bump（0.8.x → 0.9.0）。
> 如果写成 `feat(pm):` 带括号，某些 release-please 配置可能无法正确触发版本迭代。
