# SynapseERP — 架构文档索引 / Architecture Document Index

> 最后更新 / Last updated: 2026-03-25 (Phase 5.3 ✅ 完成，5.4 Tag 筛选规划中)
> 当前分支 / Branch: `main`

---

## 当前进度 / Current Progress

| 阶段 / Phase | 描述 / Description | 状态 / Status |
|---|---|---|
| **Phase 0** | 项目重组 + 基础设施 / Project restructure + infrastructure | ✅ 完成 Done |
| **Phase 1** | Vue 前端骨架 + API 基础 / Vue frontend skeleton + API foundation | ✅ 完成 Done |
| **Phase 2** | PM 核心 — Obsidian 读取 + 展示 / PM core — Obsidian read + display | ✅ 完成 Done |
| **Phase 3** | PM 进阶 — 甘特图 + 写回 / PM advanced — Gantt + write-back | ✅ 完成 Done |
| **Phase 4** | 迁移现有模块到 Vue / Migrate existing modules to Vue | ✅ 完成 Done |
| **Phase 4.5** | 端到端联调 / End-to-end integration testing | ✅ 完成 Done |
| **Phase 5** | 产品化 — 权限、多用户、实时同步、UI 升级 / Productization | 🔄 进行中 In Progress |
| Phase 6 | Docker 容器化 + 部署 / Docker containerization + deployment | ⏳ 待开始 Pending |

### Phase 0 — 步骤明细 / Step Breakdown

| 步骤 / Step | 描述 / Description | 状态 / Status |
|---|---|---|
| **0.1** | 创建 `backend/` 目录，迁移 Django 代码 / Migrate Django code into `backend/` | ✅ `0b29271` |
| **0.2** | 安装 DRF，API 基础框架 + health check / DRF setup + health check | ✅ `536693f` |
| **0.3** | 初始化 Vue 3 前端项目 / Initialize Vue 3 + Vite project | ✅ `a25c6ed` |
| **0.4** | 配置 Obsidian vault 路径 / Configure Obsidian vault path | ✅ `5cd2a0e` |

### Phase 1 — 步骤明细 / Step Breakdown

| 步骤 / Step | 描述 / Description | 状态 / Status |
|---|---|---|
| **1.1** | Vue 骨架：AppLayout、Sidebar、Router / App layout + sidebar + router | ✅ `3b37d43` |
| **1.2** | Pinia stores + Axios API client / State management + HTTP client | ✅ `2cc0a2a` |
| **1.3** | Dashboard 首页 Vue 化 / Migrate dashboard to Vue | ✅ `6770c35` |

### Phase 2 — 步骤明细 / Step Breakdown

| 步骤 / Step | 描述 / Description | 状态 / Status |
|---|---|---|
| **2.1** | 创建 `synapse_pm` Django App + Models / Create PM app + DB models | ✅ `3d9f20e` |
| **2.2** | Backend Adapter 抽象层 / PMBackendAdapter abstract layer | ✅ `de6ca5e` |
| **2.3** | VaultReader + VaultWriter / Obsidian read + write | ✅ `8434066` |
| **2.4** | SQLite 缓存同步 / Vault-to-SQLite cache sync | ✅ `3cf45e9` |
| **2.5** | DRF API — PM 数据接口 / PM REST API endpoints | ✅ `22c3fe7` |
| **2.6** | Vue 前端 — 项目列表 + 任务视图 / ProjectList + TaskDetail views | ✅ `2c45168` |

### Phase 3 — 步骤明细 / Step Breakdown

| 步骤 / Step | 描述 / Description | 状态 / Status |
|---|---|---|
| **3.1** | 集成 frappe-gantt / Integrate frappe-gantt chart | ✅ `1ebc3e8` |
| **3.2** | 甘特图交互 — 拖拽修改 / Gantt drag-and-drop interactions | ✅ `1ebc3e8` |
| **3.3** | VaultWriter 集成 — 写回 Obsidian / VaultWriter write-back | ✅ `8434066` (已在 2.3 实现) |
| **3.4** | 写入 API 接口 / Write API endpoints | ✅ `22c3fe7` (已在 2.5 实现) |

### Phase 4 — 步骤明细 / Step Breakdown

| 步骤 / Step | 描述 / Description | 状态 / Status |
|---|---|---|
| **4.1** | Attendance Analyzer API + Vue 页面 / DRF API + Vue views | ✅ `b906072` |
| **4.2** | BOM Analyzer API + Vue 页面 / DRF API + Vue views | ✅ `b906072` |
| **4.3** | 移除 Django 模板路由 / Remove Django template routes | ✅ `19f483c` |

### Phase 4.5 — 联调步骤明细 / Integration Test Breakdown

| 步骤 / Step | 描述 / Description | 状态 / Status |
|---|---|---|
| **L1** | 认证流程：未登录跳转 admin 登录页，成功后回 SPA | ✅ 通过 |
| **L2** | 后端 API 健康检查（health / dashboard / auth/me / pm/*） | ✅ 通过 |
| **L3** | PM 模块：项目列表 / 任务视图 / Gantt / TaskDetail Drawer | ✅ 通过 |
| **L4** | Attendance Analyzer：上传 → 分析 → 下载 | ✅ 通过 ⚠️ 中文下载仍出英文表头 |
| **L5** | BOM Analyzer：多文件上传 → 汇总 → 下载 | ✅ 通过 |
| **L6** | Gantt 拖拽：修改 deadline → 确认 → PATCH API → 刷新验证 | ✅ 通过 ⚠️ 交互体验待优化（逐格移动+立即弹窗） |


### Phase 5 — 产品化步骤明细 / Productization Step Breakdown

> **架构决策 / Architectural Decision (2026-03-25)**:
> Phase 5 正式切换到 **DB-Primary + Obsidian-Mirror** 架构。
> 数据库为唯一真相源，Obsidian 作为管理员的"离线客户端"。
> 详见 `background/09_architecture_vision.md`。

| 步骤 / Step | 描述 / Description | 状态 / Status |
|---|---|---|
| **5.1** | **Bug 修复 + 已知问题 / Bug fixes + known issues** | ✅ 完成 Done |
|         | fix: 考勤下载中文版仍出英文表头 / Attendance zh-Hans download shows English headers | |
|         | improve: 甘特图拖拽交互（真正拖拽代替逐格移动+立即弹窗）/ Gantt drag UX | |
|         | improve: Admin 登录页美化 / Admin login page styling | |
| **5.2** | **DB-Primary 架构清理 / DB-Primary architecture cleanup** | ✅ 完成 Done |
|         | 移除 vault/database 切换开关 / Remove vault/database switch mechanism | |
|         | API 始终使用 DatabaseAdapter / API always uses DatabaseAdapter | |
|         | 补全项目 CRUD 端点 / Add missing Project CRUD endpoints | |
| **5.3** | **Obsidian 同步服务 / Obsidian sync service** | ✅ 完成 Done |
|         | 创建独立的 ObsidianSyncService（导入+导出）/ Standalone sync service (import+export) | |
|         | Vault 路径动态配置（Admin 界面 + API）/ Vault path dynamic config (Admin UI + API) | |
|         | 冲突策略：最近修改胜出 / Conflict: last-modified-wins | |
|         | 前端 Obsidian Sync 设置页面 / Frontend SyncSettings view | |
| **5.4** | **Tag 筛选 + 项目可见性 / Tag filtering + project visibility** | ⏳ |
|         | Project/Task 模型增加 `tags` 字段 / Add `tags` field to Project/Task models | |
|         | 前端 Tag 筛选器（多选下拉）/ Tag filter UI (multi-select dropdown) | |
|         | 会议模式：一键隐藏个人项目 / Meeting mode: one-click hide personal projects | |
| **5.5** | **Vault 自动同步 / Vault auto-sync** | ⏳ |
|         | 文件监听方案（watchdog/inotify）代替轮询 / File watcher (watchdog/inotify) instead of polling | |
|         | 变更事件触发增量同步 / Change events trigger incremental sync | |
|         | 低 CPU/内存占用设计 / Low CPU/memory footprint design | |
| **5.6** | **UI/UX 全面升级 / UI/UX overhaul** | ⏳ |
|         | Dashboard 重新设计（美观 + 性能）/ Dashboard redesign (beautiful + performant) | |
|         | 响应式布局（手机/平板友好）/ Responsive layout (mobile/tablet friendly) | |
|         | 长时间后台运行优化 / Long-running background optimization | |
| **5.7** | **权限系统 + 多用户 / Permission system + multi-user** | ⏳ |
|         | JWT 认证替代 Django Session / JWT auth replacing Django Session | |
|         | 用户角色（admin / editor / viewer）/ User roles (admin / editor / viewer) | |
|         | 自定义登录/注册页面 / Custom login/register pages | |
|         | 基于 Tag 的项目访问控制 / Tag-based project access control | |
| **5.8** | **Plugin API 框架 / Plugin API framework** | ⏳ |
|         | `SynapseModule` 基类 + 标准接口 / Base class + standard interface | |
|         | 每个模块注册可用操作 / Each module registers available actions | |
|         | 为 AI Agent (MCP/OpenClaw) 预留接口 / Reserve interface for AI Agents | |
| **5.9** | **Docker Compose 部署 / Docker Compose deployment** | ⏳ |
|         | docker-compose.yml (Nginx + Django + Vue + PostgreSQL) | |
|         | 开发/生产双模式 / Dev/prod dual mode | |
|         | 一键 `docker compose up` 启动 / One-command startup | |

#### Phase 5 原始需求追溯 / Original Requirements Traceability

| 原始需求 # | 映射到步骤 / Mapped to Step | 备注 / Notes |
|---|---|---|
| #1 按 Tag 显示、隐藏个人项目 | 5.4 | 增加 tags + 会议模式 |
| #2 Vault 自动同步 | 5.5 | 用 watchdog 文件监听，不轮询 |
| #3 界面太丑 | 5.6 | Dashboard 重设计 + 响应式 |
| #4 低资源占用、手机使用 | 5.5 + 5.6 | 监听方案 + 响应式布局 |
| #5 OpenClaw / AI 集成 | 5.8 | 预留 Plugin API，不实现 AI 代码 |
| #6 Docker Compose | 5.9 | 多容器组合，不做巨大镜像 |
| #7 Vault 路径动态配置 | 5.3 | 合并到同步服务中 |
| #8 价值定位 + 多用户 | 5.7 + 09 文档 | 权限系统 + 架构愿景文档 |
| 🆕 DB-Primary 架构清理 | 5.2 | 移除切换开关，补全 CRUD |
| 🆕 Obsidian 同步服务 | 5.3 | 独立双向同步，替代旧适配器 |
| ⚠️ 考勤中文下载 Bug | 5.1 | ✅ 已修复 |
| ⚠️ 甘特图拖拽体验 | 5.1 | ✅ 已修复 |
| ⚠️ Admin 页面丑 | 5.1 | ✅ 已修复 |

---

## 文档地图 / Document Map

本目录分为两个子文件夹：
*This directory is split into two subfolders:*

```
docs/architecture/
├── 00_INDEX.md                          ← 你在这里 / You are here
│
├── plan/                                开发时随时翻阅 / Active references while coding
│   ├── 09_implementation_plan.md        完整 6-Phase 路线图（从这里开始）
│   │                                    Full 6-Phase roadmap (start here)
│   ├── 10_api_spec.md                   REST API 请求/响应契约
│   │                                    REST API request/response contracts
│   ├── 11_obsidian_parsing_rules.md     VaultReader/Writer 正则 + 路径规则
│   │                                    VaultReader/Writer regex + path rules
│   └── 12_frontend_config.md            Vite / TS / Router / Pinia 精确配置
│                                        Vite / TS / Router / Pinia exact config
│
├── background/                          当前有效的架构决策 / Active architectural decisions
│   ├── 02_obsidian_integration_design.md Obsidian ↔ Synapse 数据模型映射 / Data model mapping
│   ├── 05_para_mapping.md               PARA 层级的正确理解 / PARA hierarchy correctly understood
│   ├── 08_final_tech_stack.md           最终确认的技术栈 + 选型理由 / Final confirmed tech stack
│   ├── 09_architecture_vision.md        架构愿景与竞争优势 / Architecture vision & competitive advantage
│   │
│   └── archived/                        历史决策，已归档 / Historical decisions, archived
│       ├── 01_current_state_analysis.md  重构前的项目现状 / Pre-refactor project state
│       ├── 03_frontend_tech_decision.md  HTMX vs Vue 决策过程 / HTMX vs Vue decision process
│       ├── 06_vue3_spa_architecture.md   Vue 3 架构方案评估 / Vue 3 architecture evaluation
│       └── 07_vue_vs_python_clarification.md Vue ≠ Python 替代品 / Vue ≠ Python replacement
│
└── (04_old_plan_deprecated.md 已删除 — 被 plan/09 完全取代)
```

### 推荐阅读路线 / Recommended Reading Path

- **新人入门（5 分钟）/ Newcomer (5 min):** `background/08_final_tech_stack.md` → `background/09_architecture_vision.md`
- **开始编码 / Start coding:** `plan/09_implementation_plan.md` → `plan/10_api_spec.md`
- **PM 模块开发 / PM module dev:** `plan/11_obsidian_parsing_rules.md` + `background/02_obsidian_integration_design.md`
- **深度历史 / Deep history:** `background/archived/` 目录，看一遍即可 / read once if curious

---

## 已确认技术栈 / Confirmed Tech Stack

| 层级 / Layer | 技术 / Technology |
|---|---|
| 后端框架 / Backend framework | Django 5.x + Django REST Framework |
| 后端语言 / Backend language | Python 3.12 |
| 数据库 / Database | SQLite (dev) → PostgreSQL (prod) |
| 前端框架 / Frontend framework | Vue 3 (Composition API) + TypeScript |
| 构建工具 / Build tool | Vite 6 |
| UI 组件库 / UI component library | Naive UI |
| 状态管理 / State management | Pinia |
| 路由 / Router | Vue Router 4 |
| HTTP 客户端 / HTTP client | Axios |
| 甘特图 / Gantt chart | frappe-gantt |
| 包管理器 / Package manager | pnpm |
| 容器化 / Containerization | Docker Compose（Phase 5） |

---

## 关键架构决策 / Key Architectural Decisions

| 决策 / Decision | 结论 / Choice | 参考文档 / Reference |
|---|---|---|
| 前端方案 / Frontend approach | Vue 3 SPA（前后端分离）/ full separation | `background/03` |
| UI 库 / UI library | Naive UI（原生 TS + Composition API）| `background/08` |
| Obsidian 集成 / Obsidian integration | DB-Primary + Obsidian-Mirror（Phase 5 架构升级）| `background/09` |
| PARA 暴露 / PARA exposure | UI 不暴露 PARA 术语，用通用 PM 语言 / Hidden, generic PM terminology | `background/05` |
| Django 模板 / Django templates | Phase 4 全部删除（全面 Vue 化）/ Removed in Phase 4 | `plan/09` |
| Docker 时机 / Docker timing | Phase 5.8（PM 模块稳定后）/ After PM module is stable | `plan/09` |
| AI 集成策略 / AI integration | 预留 Plugin API，不写 AI 代码 / Reserve Plugin API, no AI code yet | `background/09` |

---

## 目标仓库结构 / Target Repository Structure (after Phase 0)

```
SynapseERP.git/
├── backend/                  Django 后端 / Django backend (Python)
│   ├── src/
│   │   ├── synapse/
│   │   ├── synapse_dashboard/
│   │   ├── synapse_attendance/
│   │   ├── synapse_bom_analyzer/
│   │   └── synapse_pm/       ← Phase 2 新增 / added in Phase 2
│   ├── synapse_project/
│   ├── manage.py
│   └── requirements.txt
├── frontend/                 Vue 3 SPA（✅ Phase 0 Step 0.3 已完成）
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── synapse                   统一入口脚本 / Unified entry point (./synapse <cmd>)
├── docker/                   Docker 配置（Phase 5 新增 / added in Phase 5）
├── docs/
│   └── architecture/         ← 本目录 / this folder
├── assets/
├── README.md
└── LICENSE
```
