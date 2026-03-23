# SynapseERP — 架构文档索引 / Architecture Document Index

> 最后更新 / Last updated: 2026-03-23 (Phase 3 甘特图 + Phase 4 Vue 迁移完成)
> 当前分支 / Branch: `refactor/pm`

---

## 当前进度 / Current Progress

| 阶段 / Phase | 描述 / Description | 状态 / Status |
|---|---|---|
| **Phase 0** | 项目重组 + 基础设施 / Project restructure + infrastructure | ✅ 完成 Done |
| **Phase 1** | Vue 前端骨架 + API 基础 / Vue frontend skeleton + API foundation | ✅ 完成 Done |
| **Phase 2** | PM 核心 — Obsidian 读取 + 展示 / PM core — Obsidian read + display | ✅ 完成 Done |
| **Phase 3** | PM 进阶 — 甘特图 + 写回 / PM advanced — Gantt + write-back | ✅ 完成 Done |
| **Phase 4** | 迁移现有模块到 Vue / Migrate existing modules to Vue | ✅ 完成 Done |
| **Phase 4.5** | 端到端联调 / End-to-end integration testing | 🔄 进行中 In progress |
| Phase 5 | Docker 容器化 / Docker containerization | ⏳ 待开始 Pending |
| Phase 6 | 持续扩展 / Ongoing extensions | ⏳ 长期 Long-term |

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
| **L1** | 认证流程：未登录跳转 admin 登录页，成功后回 SPA | 🔄 |
| **L2** | 后端 API 健康检查（health / dashboard / auth/me / pm/*） | 🔄 |
| **L3** | PM 模块：项目列表 / 任务视图 / Gantt / TaskDetail Drawer | 🔄 |
| **L4** | Attendance Analyzer：上传 → 分析 → 下载 | 🔄 |
| **L5** | BOM Analyzer：多文件上传 → 汇总 → 下载 | 🔄 |
| **L6** | Gantt 拖拽：修改 deadline → 确认 → PATCH API → 刷新验证 | 🔄 |

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
└── background/                          决策历史，看一遍就够 / Decision history, read once
    ├── 01_current_state_analysis.md     重构前的项目现状 / Project state before refactor
    ├── 02_obsidian_integration_design.md Obsidian ↔ Synapse 数据模型映射 / Data model mapping
    ├── 03_frontend_tech_decision.md     HTMX vs Vue SPA 对比 / HTMX vs Vue SPA comparison
    ├── 04_old_plan_deprecated.md        ⚠️ 已过时，被 09 取代 / OUTDATED, superseded by 09
    ├── 05_para_mapping.md               PARA 层级的正确理解 / PARA hierarchy correctly understood
    ├── 06_vue3_spa_architecture.md      Vue 3 架构方案评估 / Vue 3 architecture options evaluated
    ├── 07_vue_vs_python_clarification.md Vue 替代的是模板，不是 Python / Vue replaces templates, NOT Python
    └── 08_final_tech_stack.md           最终确认的技术栈 + 选型理由 / Final confirmed tech stack + rationale
```

### 推荐阅读路线 / Recommended Reading Path

- **快速上手（5 分钟）/ Quick catch-up (5 min):** `background/08_final_tech_stack.md` → `plan/09_implementation_plan.md`
- **编码参考 / Coding reference:** `plan/` 目录，开发时随时查阅 / keep open while working
- **深度背景 / Deep background:** `background/` 目录，看一遍即可 / read once, then archived mentally

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
| Obsidian 集成 / Obsidian integration | 可切换 Backend Adapter 模式 / Switchable Backend Adapter | `background/08` |
| PARA 暴露 / PARA exposure | UI 不暴露 PARA 术语，用通用 PM 语言 / Hidden, generic PM terminology | `background/05` |
| Django 模板 / Django templates | Phase 4 全部删除（全面 Vue 化）/ Removed in Phase 4 | `plan/09` |
| Docker 时机 / Docker timing | Phase 5（PM 模块稳定后）/ After PM module is stable | `plan/09` |

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
