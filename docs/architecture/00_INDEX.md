# SynapseERP — 架构文档索引 / Architecture Document Index

> **最后更新 / Last updated**: 2026-03-26 (Phase 5.7 ✅ 完成，Phase 5.9 🔄 进行中)
> **当前分支 / Branch**: `main`
> **目标受众 / Target Audience**: AI Agents + 项目团队

---

## 🎯 AI Agent 快速入门 / Quick Start for AI Agents (3 min)

### 每次开始工作前，按以下顺序阅读：

1. **📍 你在这里** ← 这个文件，理解整个项目的认知结构和进度
2. **🗺️ `plan/13_codebase_map.md`** — 代码库全景图（替代全盘代码扫描，节省 50% 时间）
3. **🔨 当前 Phase 计划** — 如果实现 Phase 5.9：读 `plan/15_phase59_plan.md`
4. **📖 其他参考文档** — 按需查阅（见下方文档地图）

### ✨ 关键原则

- **每次完成一个 STEP，就立即 commit** — 不要等全部完成再 commit
- **Commit message 格式严格** — 遵循规范便于历史追溯
- **修改代码后更新 `plan/13_codebase_map.md`** — 保持代码库地图与实现同步
- **所有计划都在 `docs/` 中** — 不要靠口头指示，一切写成文档

### 📊 强制阅读清单（75 分钟）

| 任务 | 优先级 | 时间 | 位置 |
|---|---|---|---|
| 本索引文件 (快速入门部分) | 🔴 必须 | 5 min | 你在这里 |
| 代码库地图 | 🔴 必须 | 20 min | `plan/13_codebase_map.md` |
| 当前 Phase 计划 (Phase 5.9) | 🔴 必须 | 30 min | `plan/15_phase59_plan.md` |
| 技术栈 + 架构愿景 | 🟡 推荐 | 20 min | `background/08 + 09` |
| API 规范 | 🟢 可选 | 15 min | `plan/10_api_spec.md` |

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

---

## 🧠 AI Agent 认知流水线 / Cognitive Pipeline

### 第 0 层：项目背景认知 (必须)

**文件**: `background/08_final_tech_stack.md` + `09_architecture_vision.md`

**你需要理解的 5 个关键点**：

1. **技术栈**
   - Backend: Django 5.x + DRF + Gunicorn
   - Frontend: Vue 3 + TypeScript + Vite
   - Database: SQLite (dev) → PostgreSQL (prod)
   - Deployment: Nginx + Systemd (prod), Docker Compose (dev/docker)

2. **架构决策: DB-Primary + Obsidian-Mirror**
   - 数据库是唯一真相源 (single source of truth)
   - Obsidian 是"离线客户端"（可选的双向同步）
   - 不要混淆：这不是 Obsidian-First 架构

3. **项目的 5 层责任分工**
   - UI (Vue) — 展示、交互
   - API (DRF) — 业务逻辑、权限
   - ORM (Django ORM) — 数据访问抽象
   - Backend Adapter — 插件化（DB vs Vault，留作扩展）
   - Sync Service — Obsidian ↔ DB 双向同步（可选）

4. **当前产品状态**
   - 已完成: 基础架构、PM 核心、多用户权限、Tag 访问控制
   - 进行中: PostgreSQL 迁移 + Docker Compose (Phase 5.9)
   - 待做: Plugin API、生产部署、Kubernetes

5. **项目规模**
   - ~1500 行 Python 代码 (backend)
   - ~1000 行 TypeScript 代码 (frontend)
   - 2 个模块稳定 (PM、Attendance)，1 个模块基础 (BOM Analyzer)
   - 500+ 个测试用例（测试覆盖中等）

### 第 1 层：当前代码库状态 (必须)

**文件**: `plan/13_codebase_map.md`

**这个文件告诉你**：
- 每个 Django app 的职责和主要文件
- 每个 Vue 组件的层级和状态管理关系
- 数据库模型的完整字段列表
- 关键 API 端点的请求/响应格式
- 已知的 Bug 和 TODO

**读这个文件而不是扫描整个代码库**，节省 50% 的时间。

### 第 2 层：当前任务计划 (必须)

**当前活跃的 Phase**:
- **Phase 5.9**: `plan/15_phase59_plan.md`

**读计划文档时，你会获得**：
- 为什么要做这个 Phase（4 个驱动力）
- 这个 Phase 分为多少个 STEP（14 步）
- 每个 STEP 的具体目标、文件位置、完整代码示例
- **最重要：每个 STEP 的规范 commit message**
- Commit 序列总结（13 个原子 commit）
- 测试验证清单（11 项可验证的检查点）

### 第 3 层：外围参考资料 (按需)

**API 规范**: `plan/10_api_spec.md`
- 所有 REST API 的请求/响应格式
- 认证方式、错误处理
- 分页、过滤、排序约定

**Obsidian 解析规则**: `plan/11_obsidian_parsing_rules.md`
- VaultReader/Writer 的正则规则
- 文件路径约定
- Frontmatter 格式

**前端配置**: `plan/12_frontend_config.md`
- Vite / TypeScript / Router 设置
- Pinia store 结构
- Naive UI 组件库用法

**历史决策**: `background/archived/`
- 看一遍即可（HTMX vs Vue、技术选型等）
- 不影响当前实现

---

## 📝 如何处理新的人类需求 / How to Handle New Human Requests

### 情景 1: 人类说"做一个新功能"

**流程**:
1. **问澄清问题** (AskUserQuestion)
   - 这个功能的业务目标是什么？
   - 涉及哪些模块（前端/后端/数据库）？
   - 是否需要修改现有 API？
   - 预期工作量是多少？

2. **写成 Phase 计划** (不是代码，是文档)
   - 在 `plan/` 中创建新文件（或扩展现有 Phase）
   - 格式参考 `15_phase59_plan.md`
   - 包含：概述、STEP 分解、Commit sequence
   - 提交给人类审核

3. **收到人类批准后，开始实现**
   - 遵循 Phase 计划中的 STEP 顺序
   - 每个 STEP 完成后立即 commit

### 情景 2: 人类发现 Bug

**流程**:
1. **创建 Bug 报告**
   - 在 `docs/bug_reports/` 中创建新 `.md` 文件（如果目录不存在就创建）
   - 记录：Bug 现象、复现步骤、预期行为、实际行为

2. **写成修复计划**
   - 可以是快速修复（1-2 commit），也可以是大的重构
   - 如果是大修复，写成小 Phase 计划

3. **修复后更新 `13_codebase_map.md`**
   - 标记 Bug 为已解决
   - 记录修改的文件和行号

### 情景 3: 人类要求重构或优化

**流程**:
1. **不要直接改代码**，先写重构计划
   - 文件名: `plan/REFACTOR_<NAME>.md`
   - 包含：为什么要重构、影响范围、实施步骤

2. **等人类批准**

3. **逐步执行**，每个 STEP 一个 commit

---

## 🔄 Commit 工作流 / Commit Workflow

### 原则

- **原子性** — 每个 commit 是一个完整、独立的功能单位
- **可追溯** — 从 commit message 就能理解做了什么、为什么做
- **逐步** — 不要积累改动等完美再 commit；每 STEP 就 commit

### Commit Message 格式

```
<type>: <subject>

<body>

<footer>
```

**Type** (强制):
- `feat:` — 新功能
- `fix:` — Bug 修复
- `docs:` — 文档更新
- `refactor:` — 代码重构（不改功能）
- `perf:` — 性能优化
- `test:` — 测试相关
- `build:` — 构建脚本 / Docker / CI
- `chore:` — 其他杂项

**Subject** (强制):
- 英文
- 不超过 70 字符
- 用现在时、主动语态 ("add" not "added")
- 开头不大写

**Body** (可选但推荐):
- 解释做了什么和为什么
- 用空行分隔 subject 和 body
- 如果是多行，用 bullet points

**Footer** (推荐):
- 关联 Phase：`Phase 5.9 Step X complete.`
- 关联 Issue：`Fixes #123`

### 示例

```
feat: add tag-based project filtering

- Add tags JSONField to Project model
- Implement _filter_projects_by_access() helper
- Update project_list view to apply tag filters
- Add /api/pm/tags/ endpoint

Phase 5.7 Step 5.4 complete.
```

### 何时 NOT Commit

- 代码编译错误 (不要 commit broken code)
- 测试失败 (不要 commit failing tests)
- 图片 / 大二进制文件 (用 git-lfs)
- .env, 密钥文件 (加入 .gitignore)

---

## 📂 文档地图 / Document Map

本目录分为多个部分：

```
docs/architecture/
├── 00_INDEX.md  ⭐ 你在这里 / You are here
│                   完整索引 + 进度表 + 工作流程指南
│
├── plan/              开发时随时翻阅 / Active references while coding
│   ├── 09_implementation_plan.md    完整 6-Phase 路线图
│   ├── 10_api_spec.md               REST API 请求/响应契约
│   ├── 11_obsidian_parsing_rules.md VaultReader/Writer 正则 + 路径规则
│   ├── 12_frontend_config.md        Vite / TS / Router / Pinia
│   ├── 13_codebase_map.md           ⭐ AI Agent 代码库地图 (必读)
│   ├── 14_phase57_plan.md           ✅ Phase 5.7 JWT + 权限系统 (已完成)
│   └── 15_phase59_plan.md           🔄 Phase 5.9 PostgreSQL + Docker (进行中)
│
├── background/        当前有效的架构决策 / Active architectural decisions
│   ├── 02_obsidian_integration_design.md
│   ├── 05_para_mapping.md
│   ├── 08_final_tech_stack.md
│   ├── 09_architecture_vision.md
│   └── archived/     历史决策，已归档
│       ├── 01_current_state_analysis.md
│       ├── 03_frontend_tech_decision.md
│       ├── 06_vue3_spa_architecture.md
│       └── 07_vue_vs_python_clarification.md
│
└── README.zh.md      中文项目 README

docs/bug_reports/  (按需创建)
├── BUG_001_...md
└── ...
```

### 何时创建新文档

1. **开始新 Phase** → 在 `plan/` 中创建 `1X_phase5X_plan.md`
2. **发现 Bug** → 在 `docs/bug_reports/` 中创建报告
3. **做大型重构** → 在 `plan/` 中创建 `REFACTOR_<name>.md`
4. **更新 Phase 进度** → 编辑本文件的进度表

### 何时更新现有文档

1. **每次修改代码** → 更新 `plan/13_codebase_map.md` 对应章节
2. **完成 STEP** → 更新本文件的进度表
3. **发现新 Bug** → 在 `plan/13_codebase_map.md` 的"已知问题"中记录

---

## ⚠️ AI Agent 常见陷阱 / Common AI Agent Pitfalls

### ❌ 陷阱 1: 一次性实现所有 STEP，最后才 commit

**错误做法**: 编辑文件 1 → 编辑文件 2 → ... → 最后 git commit

**正确做法**: 编辑文件 1 → git commit → 编辑文件 2 → git commit → ...

**原因**: 便于审核、回滚、历史追溯。

### ❌ 陷阱 2: 跳过计划文档，直接改代码

**错误**: "我觉得我知道该怎么做，先写代码再说"

**正确**: 先在 `docs/` 中写计划 → 等批准 → 再实现

### ❌ 陷阱 3: 改了代码但忘记更新 `13_codebase_map.md`

**后果**: 下次 AI Agent 读文档时获得过时信息，导致错误的设计决策

### ❌ 陷阱 4: Commit message 不规范

**错误**: "fix bugs and update stuff"

**正确**: "fix: handle null tags in project filtering"

### ❌ 陷阱 5: 跳过测试，"我觉得这个没问题"

**错误**: 没运行验证命令

**正确**: 每个 commit 后都验证

---

## 🚀 启动 Phase 5.9 / Starting Phase 5.9

### 前置检查 (Pre-flight Checklist)

在开始实现前，验证以下条件：

- [ ] 已读本文件（完整）
- [ ] 已读 `plan/13_codebase_map.md`
- [ ] 已读 `plan/15_phase59_plan.md`（这份计划）
- [ ] 理解 14 个 STEP 和 commit sequence
- [ ] 本地 git 仓库是干净的 (no uncommitted changes)
- [ ] 最近的 commit 是来自 main 分支

### 开始命令

```bash
# 1. 确认在正确分支
git branch -v

# 2. 确保代码是最新的
git pull origin main

# 3. 查看当前 Phase 5.9 的状态
cat docs/architecture/plan/15_phase59_plan.md | head -50

# 4. 开始 STEP 1 的实施
# (见计划文档中的 STEP 1 详细说明)
```

---

## 📈 项目进度 - Phase 5 详解

### Phase 5 — 步骤明细 / Productization Step Breakdown

> **架构决策 / Architectural Decision (2026-03-25)**:
> Phase 5 正式切换到 **DB-Primary + Obsidian-Mirror** 架构。
> 数据库为唯一真相源，Obsidian 作为管理员的"离线客户端"。
> 详见 `background/09_architecture_vision.md`。

| 步骤 / Step | 描述 / Description | 状态 / Status |
|---|---|---|
| **5.1** | Bug 修复 + 已知问题 | ✅ 完成 Done |
| **5.2** | DB-Primary 架构清理 | ✅ 完成 Done |
| **5.3** | Obsidian 同步服务 | ✅ 完成 Done |
| **5.4** | Tag 筛选 + 项目可见性 | ✅ 完成 Done |
| **5.5** | Vault 自动同步 | ✅ 完成 Done |
| **5.6** | UI/UX 全面升级 | ✅ 完成 Done |
| **5.7** | 权限系统 + 多用户 | ✅ 完成 Done |
| **5.8** | Plugin API 框架 | ⏳ 待开始 Pending |
| **5.9** | PostgreSQL 迁移 + Docker Compose | 🔄 进行中 In Progress |

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
| 容器化 / Containerization | Docker Compose（Phase 5.9） |

---

## 关键架构决策 / Key Architectural Decisions

| 决策 / Decision | 结论 / Choice | 参考文档 / Reference |
|---|---|---|
| 前端方案 / Frontend approach | Vue 3 SPA（前后端分离） | `background/08` |
| UI 库 / UI library | Naive UI（原生 TS） | `background/08` |
| Obsidian 集成 / Obsidian integration | DB-Primary + Obsidian-Mirror（Phase 5） | `background/09` |
| PARA 暴露 / PARA exposure | UI 不暴露 PARA 术语 | `background/05` |
| Django 模板 / Django templates | Phase 4 全部删除（全面 Vue 化） | `plan/09` |
| Database 迁移 / Database migration | Phase 5.9 SQLite → PostgreSQL | `plan/15_phase59_plan.md` |
| AI 集成策略 / AI integration | 预留 Plugin API，不写 AI 代码 | `background/09` |

---

## 推荐阅读路线 / Recommended Reading Path

- **AI Agent 快速上手（必读）** → 本文档 + `plan/13_codebase_map.md` + `plan/15_phase59_plan.md`
- **新人入门（5 分钟）** → `background/08_final_tech_stack.md` → `background/09_architecture_vision.md`
- **开始编码** → `plan/09_implementation_plan.md` → `plan/10_api_spec.md`
- **实施 Phase 5.9** → `plan/15_phase59_plan.md`（含 14 步详细计划）
- **PM 模块开发** → `plan/11_obsidian_parsing_rules.md` + `background/02_obsidian_integration_design.md`
- **深度历史** → `background/archived/` 目录（看一遍即可）

---

## 目标仓库结构 / Target Repository Structure

```
SynapseERP.git/
├── backend/              Django 后端 / Django backend (Python)
│   ├── src/
│   │   ├── synapse/
│   │   ├── synapse_dashboard/
│   │   ├── synapse_attendance/
│   │   ├── synapse_bom_analyzer/
│   │   └── synapse_pm/
│   ├── synapse_project/
│   ├── manage.py
│   └── requirements.txt
├── frontend/            Vue 3 SPA / Vue 3 frontend (TypeScript)
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── docker/              Docker 配置 / Docker files (Phase 5.9)
│   ├── Dockerfile
│   ├── Dockerfile.frontend
│   ├── entrypoint.sh
│   └── nginx/
├── docs/               ← 你在这里 / You are here
│   └── architecture/
├── synapse             统一入口脚本 / Unified entry point
├── .gitignore
├── README.md
└── LICENSE
```

---

**🎯 一切准备就绪，可以开始工作！**

请按本文档的 "AI Agent 快速入门" 部分开始阅读。

