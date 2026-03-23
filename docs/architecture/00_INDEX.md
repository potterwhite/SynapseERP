# SynapseERP — 架构文档索引 / Architecture Document Index

> 最后更新 / Last updated: 2026-03-23
> 当前分支 / Branch: `refactor/pm`

---

## 当前进度 / Current Progress

| 阶段 / Phase | 描述 / Description | 状态 / Status |
|---|---|---|
| **Phase 0** | 项目重组 + 基础设施 / Project restructure + infrastructure | 🔄 进行中 In Progress |
| Phase 1 | Vue 前端骨架 + API 基础 / Vue frontend skeleton + API foundation | ⏳ 待开始 Pending |
| Phase 2 | PM 核心 — Obsidian 读取 + 展示 / PM core — Obsidian read + display | ⏳ 待开始 Pending |
| Phase 3 | PM 进阶 — 甘特图 + 写回 / PM advanced — Gantt + write-back | ⏳ 待开始 Pending |
| Phase 4 | 迁移现有模块到 Vue / Migrate existing modules to Vue | ⏳ 待开始 Pending |
| Phase 5 | Docker 容器化 / Docker containerization | ⏳ 待开始 Pending |
| Phase 6 | 持续扩展 / Ongoing extensions | ⏳ 长期 Long-term |

### Phase 0 — 步骤明细 / Step Breakdown

| 步骤 / Step | 描述 / Description | 状态 / Status |
|---|---|---|
| **0.1** | 创建 `backend/` 目录，迁移 Django 代码 / Create `backend/` dir, migrate Django code | ✅ 完成 commit `0b29271` |
| **0.2** | 安装 DRF，创建 API 基础框架 + health check / Install DRF, create API foundation + health check | ⏳ 下一步 Next |
| 0.3 | 初始化 Vue 3 前端项目 / Initialize Vue 3 frontend project | ⏳ 待开始 Pending |
| 0.4 | 配置 Obsidian vault 路径 / Configure Obsidian vault path | ⏳ 待开始 Pending |

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
│   ├── requirements.txt
│   └── run.sh
├── frontend/                 Vue 3 SPA（Phase 0 Step 0.3 新增 / added in Step 0.3）
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── docker/                   Docker 配置（Phase 5 新增 / added in Phase 5）
├── docs/
│   └── architecture/         ← 本目录 / this folder
├── assets/
├── README.md
└── LICENSE
```
