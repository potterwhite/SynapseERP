# 最终技术选型决策

> 日期：2026-03-21
> 状态：最终决策

---

## 一、确定的技术栈

| 层级 | 技术 | 理由 |
|------|------|------|
| **后端框架** | Django 5.x + DRF | 保留现有，仅添加 REST API |
| **后端语言** | Python 3.12 | 不变 |
| **数据库** | SQLite (dev) → PostgreSQL (prod) | 不变 |
| **前端框架** | **Vue 3 (Composition API)** | 用户选择 |
| **前端语言** | **TypeScript** | 类型安全，长期项目必须 |
| **构建工具** | **Vite 6** | Vue 官方推荐，最快 |
| **UI 组件库** | **Naive UI** | 见下方分析 |
| **状态管理** | **Pinia** | Vue 3 官方推荐 |
| **路由** | **Vue Router 4** | SPA 必须 |
| **HTTP 客户端** | **Axios** | 拦截器、错误处理最成熟 |
| **甘特图** | **frappe-gantt** (起步) | MIT 协议、轻量、快速出效果 |
| **CSS 方案** | **Naive UI 内置** + CSS Variables | 随组件库 |
| **包管理器** | **pnpm** | 比 npm 快、节省磁盘 |
| **Docker** | **docker-compose** | Phase 3 实施 |

---

## 二、为什么选 Naive UI 而不是 Element Plus

基于你的需求——**开源、有前景、稳定、不容易过时**：

| 维度 | Element Plus | Naive UI | 胜出 |
|------|-------------|----------|------|
| **TypeScript 原生** | ⚠️ 部分 | ✅ 完全用 TS 编写 | Naive UI |
| **Composition API** | ⚠️ 混合 | ✅ 完全基于 Composition API | Naive UI |
| **树摇优化** | ✅ 支持 | ✅ 更好 | Naive UI |
| **渲染性能** | 🟡 一般 | ✅ 虚拟滚动内置 | Naive UI |
| **主题系统** | ✅ CSS Variables | ✅ 更灵活的 Theme Overrides | Naive UI |
| **包大小** | 🟡 较大 | ✅ 按需引入最小 | Naive UI |
| **文档质量** | ✅ 中文优秀 | ✅ 中/英双语，代码示例清晰 | 平手 |
| **社区规模** | ✅ 更大 (25k star) | 🟡 较小但增长快 (16k star) | Element Plus |
| **稳定性** | ✅ 饿了么团队维护 | ✅ 核心作者 unovue 持续维护 | 平手 |
| **未来前景** | ⚠️ 从 Vue 2 迁移包袱 | ✅ 从零为 Vue 3 设计 | Naive UI |

**选择 Naive UI 的核心理由：**

1. **从零为 Vue 3 + TypeScript 设计** — 没有历史包袱
2. **Composition API 原生** — 代码风格现代，与 Vue 3 最佳实践一致
3. **你的项目是开源项目** — Naive UI 的代码质量被认为是 Vue 3 组件库中最高的
4. **性能优秀** — 内置虚拟滚动，大数据量表格不卡
5. **Tree-shaking 最优** — 打包体积最小

**潜在风险：社区比 Element Plus 小。缓解方式：核心功能（表格、表单、布局）已非常成熟。**

---

## 三、关于 Obsidian 可切换开关

你提到希望 Obsidian 集成做成可切换的开关。这是完全正确的架构思维。

### 设计方案：Backend Adapter Pattern

```python
# settings.py
SYNAPSE_PM_BACKEND = "vault"  # 或 "database"
OBSIDIAN_VAULT_PATH = "/path/to/vault"  # 仅 vault 模式需要

# backend/adapters/__init__.py
class PMBackendAdapter(ABC):
    """Abstract base class for PM data backends"""
    @abstractmethod
    def get_projects(self) -> List[Project]: ...
    @abstractmethod
    def get_tasks(self, project_id) -> List[Task]: ...
    @abstractmethod
    def create_task(self, task: Task) -> Task: ...
    @abstractmethod
    def update_task(self, task_id, data) -> Task: ...

# backend/adapters/vault_adapter.py
class VaultAdapter(PMBackendAdapter):
    """Read/write Obsidian vault .md files"""
    ...

# backend/adapters/database_adapter.py
class DatabaseAdapter(PMBackendAdapter):
    """Read/write Django ORM (PostgreSQL/SQLite)"""
    ...
```

### 前端切换

```typescript
// 前端不需要知道后端是 vault 还是 database
// API 接口完全一致
GET /api/pm/projects/    // → 后端自动选择 adapter
POST /api/pm/tasks/      // → 后端自动选择 adapter
```

### 用户配置

```
Synapse Settings → PM Backend
  ○ Obsidian Vault (需要指定路径)
  ● Database (默认，无需额外配置)
```

---

## 四、仓库结构最终方案

```
SynapseERP.git/
├── backend/                         # Python Django 后端
│   ├── src/
│   │   ├── synapse/                 # Package meta
│   │   ├── synapse_dashboard/       # Dashboard app
│   │   ├── synapse_attendance/      # Attendance analyzer
│   │   ├── synapse_bom_analyzer/    # BOM analyzer
│   │   └── synapse_pm/             # 🆕 Project Management app
│   │       ├── adapters/            # 🆕 Backend adapters
│   │       │   ├── __init__.py     # Adapter factory
│   │       │   ├── base.py         # Abstract base
│   │       │   ├── vault_adapter.py # Obsidian vault R/W
│   │       │   └── db_adapter.py   # Database R/W
│   │       ├── vault/              # 🆕 Vault utilities
│   │       │   ├── reader.py       # Parse .md files
│   │       │   └── writer.py       # Write .md files
│   │       ├── api/                # 🆕 DRF API views
│   │       ├── models.py           # Django ORM models
│   │       ├── serializers.py      # DRF serializers
│   │       └── urls.py
│   ├── synapse_project/            # Django project config
│   ├── manage.py
│   ├── requirements.txt
│   └── deploy/
├── frontend/                        # 🆕 Vue 3 SPA
│   ├── src/
│   │   ├── api/                    # API 通信层
│   │   │   ├── client.ts           # Axios 配置
│   │   │   ├── pm.ts               # PM API 调用
│   │   │   ├── attendance.ts       # Attendance API 调用
│   │   │   └── bom.ts              # BOM API 调用
│   │   ├── views/                  # 页面级组件
│   │   │   ├── Dashboard.vue
│   │   │   ├── pm/
│   │   │   │   ├── ProjectList.vue
│   │   │   │   ├── TaskBoard.vue
│   │   │   │   └── GanttView.vue
│   │   │   ├── attendance/
│   │   │   │   ├── Upload.vue
│   │   │   │   └── Result.vue
│   │   │   └── bom/
│   │   │       ├── Upload.vue
│   │   │       └── Result.vue
│   │   ├── components/             # 可复用组件
│   │   │   ├── layout/
│   │   │   │   ├── AppLayout.vue
│   │   │   │   ├── Sidebar.vue
│   │   │   │   └── Header.vue
│   │   │   └── shared/
│   │   ├── stores/                 # Pinia 状态管理
│   │   │   ├── auth.ts
│   │   │   ├── pm.ts
│   │   │   └── app.ts
│   │   ├── router/                 # Vue Router
│   │   │   └── index.ts
│   │   ├── types/                  # TypeScript 类型定义
│   │   │   ├── pm.ts
│   │   │   └── api.ts
│   │   ├── App.vue                 # 根组件
│   │   └── main.ts                 # 入口文件
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── env.d.ts
├── docker/                          # 🆕 Docker 配置
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── nginx.conf
│   └── docker-compose.yml
├── docs/                            # 文档
│   └── architecture/
└── README.md
```

---

## 五、开发环境需求总结

```bash
# 后端 (Python)
Python 3.12+
pip / virtualenv

# 前端 (Node.js)
Node.js 18+ (LTS)
pnpm (替代 npm)

# Docker (Phase 3)
Docker Engine
Docker Compose v2
```
