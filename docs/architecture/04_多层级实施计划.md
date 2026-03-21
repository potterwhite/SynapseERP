# 多层级实施计划（草案）

> 评估日期：2026-03-21
> 状态：草案，待与 PotterWhite 确认后定稿

---

## 总体路线图

```
Phase 0: 基础设施准备          [1-2 天]
Phase 1: PM 核心 + Obsidian 读取  [3-5 天]
Phase 2: 甘特图 + 写回 Obsidian    [3-5 天]
Phase 3: Docker 容器化            [1-2 天]
Phase 4: 持续扩展               [长期]
```

---

## Phase 0：基础设施准备

**目标：** 为 PM 模块做好技术基础，不触碰业务逻辑。

### Step 0.1：引入 DRF API 基础框架
- 创建 `synapse_project/api.py` 作为 API 路由入口
- 配置 DRF 的 `DEFAULT_RENDERER_CLASSES` 和认证策略
- 测试 `GET /api/health/` 返回 200
- **git commit**: `feat(api): Initialize DRF API infrastructure`

### Step 0.2：引入前端基础库
- 在 `assets/` 或 `static/` 目录添加 HTMX + Alpine.js（CDN 或本地）
- 创建 `base.html` 共享模板（统一导航 + 库引入）
- 现有页面保持不变
- **git commit**: `feat(ui): Add HTMX and Alpine.js base infrastructure`

### Step 0.3：配置 Obsidian Vault 路径
- 在 `.env` 中新增 `OBSIDIAN_VAULT_PATH` 配置项
- 在 `settings.py` 中读取并验证路径存在性
- **git commit**: `feat(config): Add Obsidian vault path configuration`

---

## Phase 1：PM 核心 + Obsidian 读取

**目标：** 能从 Obsidian vault 读取 Area/Project/Task 并在 Synapse 中展示。

### Step 1.1：创建 `synapse_pm` Django App
- `python manage.py startapp synapse_pm`
- 注册到 `INSTALLED_APPS` 和 `SYNAPSE_MODULES`
- 基本 URL 路由 `/pm/`
- **git commit**: `feat(pm): Create synapse_pm app skeleton`

### Step 1.2：实现 VaultReader — 目录扫描器
- `src/synapse_pm/vault/reader.py`
- `scan_areas()`: 扫描 `2_AREA/` 子目录
- `scan_projects()`: 扫描 `1_PROJECT/` 子目录
- `scan_archive()`: 扫描 `4_ARCHIVE/` 子目录
- 返回结构化的 Python 对象列表
- **git commit**: `feat(pm): Implement VaultReader directory scanner`

### Step 1.3：实现 VaultReader — Frontmatter 解析器
- 解析 task_*.md 的 YAML frontmatter
- 解析 daily note 的时间块（用正则）
- 聚合每个 task 的实际工时
- 单元测试
- **git commit**: `feat(pm): Implement frontmatter and time block parser`

### Step 1.4：实现 SQLite 缓存层
- `src/synapse_pm/models.py`: CachedArea, CachedProject, CachedTask
- 同步命令 `python manage.py sync_vault`
- 增量同步逻辑（基于 mtime）
- **git commit**: `feat(pm): Implement vault-to-SQLite cache sync`

### Step 1.5：PM Dashboard 页面
- 项目列表视图（按 Area 分组）
- 每个项目显示：名称、任务数、完成率、总工时
- 使用 Django Templates + HTMX 筛选
- **git commit**: `feat(pm): Add PM dashboard with project overview`

### Step 1.6：DRF API — 任务数据接口
- `GET /pm/api/areas/` → 所有 Area
- `GET /pm/api/projects/` → 所有 Project（支持按 area 过滤）
- `GET /pm/api/tasks/` → 所有 Task（支持按 project/status 过滤）
- `GET /pm/api/tasks/{uuid}/` → 单个 Task 详情 + 时间记录
- **git commit**: `feat(pm): Add DRF API endpoints for PM data`

---

## Phase 2：甘特图 + 写回 Obsidian

**目标：** 可视化甘特图 + 从 Synapse 写回 Obsidian vault。

### Step 2.1：集成 frappe-gantt
- 添加 frappe-gantt 到 static 资源
- 甘特图页面 `/pm/gantt/`
- 从 API 获取数据渲染
- 支持 Area/Project/Task 三级视图切换
- **git commit**: `feat(pm): Integrate frappe-gantt chart view`

### Step 2.2：甘特图交互功能
- 拖拽修改任务时间 → 更新 API
- 点击任务 → 侧边栏详情
- 视图切换（日/周/月）
- 项目/Area 筛选
- **git commit**: `feat(pm): Add Gantt chart interactions`

### Step 2.3：实现 VaultWriter — 任务写入
- 创建新 task → 生成 task_xxx.md（遵循现有格式）
- 更新 task 状态 → 修改 frontmatter
- 原子写入 + 安全检查
- **git commit**: `feat(pm): Implement VaultWriter for task files`

### Step 2.4：实现 VaultWriter — Daily Note 写入
- 追加时间块到当天 daily note
- 如果 daily note 不存在则从模板创建
- 遵循现有的时间块格式
- **git commit**: `feat(pm): Implement daily note time block writer`

### Step 2.5：完善 API — 写入接口
- `POST /pm/api/tasks/` → 创建任务 → VaultWriter
- `PATCH /pm/api/tasks/{uuid}/` → 更新任务 → VaultWriter
- `POST /pm/api/time-entries/` → 记录时间 → VaultWriter
- **git commit**: `feat(pm): Add write API endpoints with VaultWriter`

---

## Phase 3：Docker 容器化

**目标：** 一键 `docker-compose up` 启动完整环境。

### Step 3.1：创建 Dockerfile
- 基于 `python:3.12-slim`
- 安装依赖 + collectstatic
- Gunicorn 作为 entrypoint
- **git commit**: `feat(docker): Add Dockerfile for Synapse`

### Step 3.2：创建 docker-compose.yml
- `web`: Synapse + Gunicorn
- `nginx`: 静态文件 + 反向代理
- `db`: PostgreSQL（可选，SQLite 也行）
- Volume: Obsidian vault 挂载点
- **git commit**: `feat(docker): Add docker-compose configuration`

### Step 3.3：环境配置与文档
- `.env.docker.example`
- 文档：如何配置 vault 路径
- `run.sh docker:up / docker:down` 命令
- **git commit**: `feat(docker): Add Docker deployment docs and scripts`

---

## Phase 4：持续扩展（长期）

按需开发的后续模块，不急：

| 模块 | 描述 | 触发条件 |
|------|------|----------|
| 周报/月报生成器 | 从 daily notes 聚合生成报告 | 公司需要 |
| 文件审批流 | 简单的审批链 | 公司需要 |
| 知识库搜索 | 全文搜索 Obsidian vault | 个人需要 |
| 数据看板 | ECharts 仪表盘 | 管理层需要 |
| 番茄时钟集成 | 与你的番茄时钟项目联动 | 个人需要 |

---

## 每个 Step 的执行纪律

```
每一步：
1. 明确目标和验收标准
2. 编码实现
3. 手动测试 / 单元测试
4. git add + git commit（有意义的 commit message）
5. 确认不影响现有功能
6. 进入下一步
```

---

## 待确认事项清单

| # | 问题 | 选项 | 影响范围 |
|---|------|------|----------|
| Q1 | 前端技术路线 | A: HTMX+Alpine / B: Vue SPA / C: 混合 | 全局 |
| Q2 | Area 到 Project 的映射关系 | 自动推断 vs 手动配置 | PM 模块 |
| Q3 | 甘特图库选型 | frappe-gantt vs dhtmlxGantt vs ECharts | PM 模块 |
| Q4 | 是否需要 deadline 等新字段 | 扩展 frontmatter vs 仅用现有字段 | Obsidian 兼容 |
| Q5 | Docker 优先级 | PM 之前 vs PM 之后 | 整体排期 |
| Q6 | 是否需要多用户支持 | 个人专用 vs 团队使用 | 架构决策 |
