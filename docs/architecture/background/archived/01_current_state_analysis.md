# Synapse 现状分析与战略评估

> 评估日期：2026-03-21
> 评估人：Claude (System Architect)
> 项目版本：v0.8.0-alpha

---

## 一、项目现状全景

### 1.1 技术栈总览

| 维度 | 当前选择 |
|------|----------|
| Backend Framework | Django 5.x (Python) |
| Template Engine | Django Templates (server-side rendering) |
| Database | SQLite (dev) / PostgreSQL (production-ready) |
| WSGI Server | Gunicorn |
| Reverse Proxy | Nginx |
| Data Processing | Pandas + NumPy + OpenPyXL |
| Markdown Rendering | markdown2 |
| i18n | Django i18n (zh-hans / en) |
| Deployment | Systemd + Nginx (run.sh orchestrator) |

### 1.2 模块架构

```
synapse_project/          # Django project config
├── settings.py           # SYNAPSE_MODULES registry
└── urls.py               # Root URL dispatcher

src/
├── synapse/              # Package metadata (__version__)
├── synapse_dashboard/    # Portal/Hub (placement: main_content)
├── synapse_attendance/   # Tool #1: Attendance Analyzer
└── synapse_bom_analyzer/ # Tool #2: BOM Analyzer
```

### 1.3 Loader 机制分析

当前的 "loader" 是一个**配置驱动的模块注册系统**：

```python
# settings.py
SYNAPSE_MODULES = [
    {
        "app_name": "synapse_attendance",
        "display_name": _("Attendance Analyzer"),
        "url_name": "synapse_attendance:analyze",
        "placement": "toolbox",
        "order": 10,
    },
    ...
]
```

**优点：**
- 清晰的关注点分离
- 新模块只需注册即可出现在导航中
- Django App 的天然隔离（独立 models/views/urls/templates）

**限制：**
- 注册是**静态**的（需要改 `settings.py` 并重启）
- 没有真正的运行时插件发现（如扫描目录自动加载）
- 每个模块的 UI 是**独立的 HTML 页面**（非 SPA），模块间导航是全页面跳转
- 没有统一的前端状态管理

### 1.4 当前 UI 能力

| 能力 | 状态 |
|------|------|
| Markdown 渲染 | ✅ markdown2 (通知面板) |
| 表格显示 | ✅ Pandas DataFrame → HTML |
| Excel 导入/导出 | ✅ openpyxl |
| 拖拽文件上传 | ✅ |
| 图表/可视化 | ❌ 无 |
| 甘特图 | ❌ 无 |
| 日历视图 | ❌ 无 |
| 实时更新 | ❌ 无 WebSocket/SSE |
| REST API | ❌ 无 (DRF 已在依赖中但未使用) |
| 响应式设计 | ⚠️ 基础 (inline CSS) |

---

## 二、需求逐一分析

### 需求 A：成为公司唯一软件，替代 Office/飞书

**可行性评估：⚠️ 长期可行，但需要架构演进**

**分析：**

你的愿景本质上是将 Synapse 打造成一个**内部工作平台（Workspace）**。这需要以下模块层级：

| 层级 | Office 对标 | 飞书对标 | 实现难度 |
|------|-------------|----------|----------|
| 文档协作 | Word/Docs | 文档 | 🔴 高（需协同编辑） |
| 表格分析 | Excel | 多维表格 | 🟡 中（你已经有 Pandas 基础） |
| 即时通讯 | — | IM | 🔴 极高 |
| 项目管理 | Project | 项目 | 🟢 中低（你的核心需求） |
| 审批/OA | — | 审批 | 🟡 中 |
| 数据看板 | — | 仪表盘 | 🟢 低（图表库即可） |

**架构师建议：**

不要试图一次性替代所有。采用**80/20 法则**：找到你公司 80% 的信息流通发生在哪些场景，先解决这些。大概率是：
1. **项目管理 + 任务跟踪**（你的首要需求）
2. **数据分析报告**（已有 Attendance/BOM）
3. **信息看板/通知**（已有基础）

IM 和实时文档协作建议**放弃自建**，这两者的工程量是团队级别的。

---

### 需求 B：Docker 容器化

**可行性评估：🟢 完全可行，Django 天然适合容器化**

**当前部署架构：**
```
run.sh prepare → venv + pip install → migrate
run.sh deploy  → Gunicorn + Nginx + Systemd
```

**Docker 化路径（已评估你的 deploy/ 目录）：**

```
Docker Compose 架构：
┌──────────────────────────────┐
│ docker-compose.yml           │
├──────────────────────────────┤
│  web:     Gunicorn + Django  │
│  nginx:   Static files + RP  │
│  db:      PostgreSQL         │
│  redis:   Cache (未来需要)   │
└──────────────────────────────┘

Volume Mounts:
  - ./staticfiles:/app/staticfiles
  - db_data:/var/lib/postgresql/data
  - ./obsidian_vault:/mnt/obsidian  # <-- 关键：挂载 Obsidian
```

**你已经有的优势：**
- `deploy/nginx.conf.template` → 直接复用
- `deploy/synapse.service.template` → 对应 `docker-compose` 的 `web` service
- `requirements.txt` 完备
- `.env` 环境变量机制已就绪

**评估：这是一个 1-2 天的工作量**，可以在任何阶段插入。不阻塞其他工作。

---

### 需求 C：Project Management + 甘特图

**可行性评估：🟢 完全可行，是最有价值的下一个模块**

这正是 Synapse 的 loader 架构最适合承载的——作为一个新的 `synapse_pm` Django App。

**甘特图技术选型分析：**

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **frappe-gantt** | 轻量、纯 JS、MIT 协议、交互优秀 | 无依赖日历视图 | ⭐⭐⭐⭐ |
| **dhtmlxGantt** | 功能最全、企业级 | 免费版功能受限 | ⭐⭐⭐ |
| **TOAST UI Calendar** | 日历+甘特、MIT | 甘特功能较弱 | ⭐⭐ |
| **D3.js 自绘** | 完全可控 | 开发量大 | ⭐ |
| **Apache ECharts Gantt** | 渲染性能好 | 交互定制复杂 | ⭐⭐⭐ |

**推荐：frappe-gantt 作为起步** — 轻量、无依赖、与 Django 后端配合简单。

---

### 需求 D：与 Obsidian 融合

**可行性评估：🟢🟢🟢 不仅可行，而且是你项目最大的差异化优势**

**核心洞察：Obsidian 的 vault 就是一个纯文件系统的 markdown 仓库。**

这意味着：
1. Synapse（Django）可以直接**读写** Obsidian vault 目录下的 `.md` 文件
2. 所有数据都是人类可读的 markdown — 不存在数据库锁定
3. Synapse 和 Obsidian 可以**同时操作同一批文件**，互不干扰

**融合架构：**

```
┌─────────────────────────────────────────────┐
│              Obsidian Vault (文件系统)        │
│  ~/syncthing/ObsidianVault/PARA-Vault/      │
│                                              │
│  ┌───────────────────┐  ┌─────────────────┐ │
│  │ Obsidian Desktop  │  │ Synapse (Django) │ │
│  │  - 编辑 markdown  │  │  - 解析 markdown │ │
│  │  - Dataview 渲染  │  │  - 生成甘特图    │ │
│  │  - Templater 模板 │  │  - 写入 daily    │ │
│  │  - 手动操作       │  │  - REST API     │ │
│  └───────────────────┘  └─────────────────┘ │
│          ↕ 读/写 .md 文件    ↕ 读/写 .md    │
│  ┌─────────────────────────────────────────┐ │
│  │          PARA-Vault/*.md 文件            │ │
│  │  1_PROJECT/  2_AREA/  3_RESOURCE/       │ │
│  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

**你的 Obsidian 数据格式已经天然适配：**

1. **Task 文件**有 YAML frontmatter：
```yaml
---
task_uuid: 693d3007-e356-418f-9863-5d8a3fe38b89
task_name: task_xxx
project: "[[2025.19_Project_Synapse]]"
created: 2026-03-21
status: todo
priority: medium
tags: journal/task
---
```

2. **Daily Note** 有结构化的时间块：
```markdown
- [ ] 任务描述 (start:: 08:10) (end:: 10:00) (task_uuid:: xxx) (task_name:: [[task_xxx]])
```

3. **PARA 层级**是纯目录结构：
```
1_PROJECT/ → 所有项目
2_AREA/    → 所有领域（项目的上层分类）
4_ARCHIVE/ → 已完成项目
```

**Synapse 需要做的：**
- 一个 `VaultReader` 服务类：扫描指定目录，解析 YAML frontmatter + markdown
- 一个 `VaultWriter` 服务类：按照你现有的模板格式写入 daily note 的时间块
- 前端甘特图从 vault 数据渲染

**这就是你说的"把 obsidian 内部数据库开放出来"——而技术上 obsidian 根本没有数据库，只有文件，所以 Synapse 天然可以读。**

**关于特殊内容（图表等）的处理：**
- 甘特图 → Synapse Web 端渲染，可以导出为 PNG 或 SVG
- 图表在 Obsidian 中 → 用 `![[chart.png]]` 引用（Obsidian 支持嵌入图片）
- 或者用 Mermaid 语法（Obsidian 原生支持 Mermaid Gantt）

---

## 三、关键风险与约束

| 风险 | 影响 | 缓解策略 |
|------|------|----------|
| 前端能力不足（当前是 Django 模板 SSR） | 甘特图等交互式 UI 受限 | 引入轻量前端库（HTMX 或 Alpine.js），不做全 SPA |
| Obsidian 文件被同时写入导致冲突 | 数据丢失 | 使用文件锁 + 原子写入；Syncthing 已提供版本管理 |
| 个人项目精力有限 | 进度缓慢 | 严格按优先级排列，每个 milestone 独立可用 |
| SQLite 在并发下性能差 | 多用户场景卡顿 | Docker 化后切 PostgreSQL |

---

## 四、技术债务清单

1. **前端无统一框架** — 每个模块独立 HTML + inline CSS
2. **无 REST API** — DRF 在依赖中但未使用
3. **无前端构建系统** — 无 webpack/vite/tailwind
4. **Session-based 状态** — 不适合多设备访问
5. **无自动化测试** — `dev:test` 命令存在但测试用例为空

---

## 五、战略总结

| 需求 | 可行性 | 优先级 | 建议 |
|------|--------|--------|------|
| Project Management + 甘特图 | 🟢 高 | P0 | 第一个做，最高 ROI |
| Obsidian 融合 | 🟢 高 | P0 | 与 PM 模块一起做，它们是同一件事 |
| Docker 容器化 | 🟢 高 | P1 | PM 模块稳定后立即做 |
| 替代 Office/飞书 | ⚠️ 长期 | P2+ | 逐步添加工具模块 |
