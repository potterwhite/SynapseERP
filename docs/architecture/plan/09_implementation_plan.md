# 最终实施计划（已确认版）

> 日期：2026-03-21
> 状态：基于全部决策的完整路线图
>
> 技术栈确认：
> - 后端：Django 5.x + DRF (Python)
> - 前端：Vue 3 + TypeScript + Naive UI + Vite
> - 甘特图：frappe-gantt
> - Obsidian：可切换 Backend Adapter
> - 容器化：Docker Compose

---

## 总体路线图（修订版）

```
Phase 0: 项目重组 + 基础设施                [2-3 天]
Phase 1: Vue 前端骨架 + API 基础            [3-4 天]
Phase 2: PM 核心 — Obsidian 读取 + 展示     [4-5 天]
Phase 3: PM 进阶 — 甘特图 + 写回 Obsidian   [3-4 天]
Phase 4: 迁移现有模块到 Vue                  [2-3 天]
Phase 5: Docker 容器化                      [1-2 天]
Phase 6: 持续扩展                           [长期]

总计核心工作量：约 15-21 天
```

---

## Phase 0：项目重组 + 基础设施

**目标：** 建立 Monorepo 结构，前后端分离的基础。现有功能不受影响。

---

### Step 0.1：创建 backend/ 目录，迁移 Django 代码

**详细操作：**
- 创建 `backend/` 目录
- 将 `src/`, `synapse_project/`, `manage.py`, `requirements.txt`, `deploy/`, `locale/`, `tools/`, `run.sh`, `pyproject.toml` 移入 `backend/`
- 更新 `manage.py` 和 `settings.py` 中的路径引用
- 验证 `cd backend && ./run.sh run` 仍然正常工作

**验收标准：**
- [x] Django dev server 正常启动
- [x] 所有现有功能正常
- [x] Git 历史保留（`git mv`）

**git commit:** `refactor(project): Move Django code into backend/ directory`

---

### Step 0.2：安装 DRF 并创建 API 基础框架

**详细操作：**
- DRF 已在 `requirements.txt` 中，无需安装
- 创建 `backend/synapse_project/api_urls.py` — API 路由入口
- 在 `settings.py` 中配置 DRF：
  ```python
  REST_FRAMEWORK = {
      'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
      'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser', 'rest_framework.parsers.MultiPartParser'],
      'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.SessionAuthentication'],
      'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
  }
  ```
- 添加 health check endpoint: `GET /api/health/` → `{"status": "ok"}`

**验收标准：**
- [x] `curl http://localhost:8000/api/health/` 返回 `{"status": "ok"}`
- [x] 现有页面不受影响

**git commit:** `feat(api): Initialize DRF API infrastructure with health check`

---

### Step 0.3：初始化 Vue 3 前端项目

**详细操作：**
```bash
cd SynapseERP.git
pnpm create vite frontend -- --template vue-ts
cd frontend
pnpm install
pnpm install naive-ui @vicons/ionicons5
pnpm install vue-router@4 pinia axios
pnpm install -D @types/node
```

- 配置 `vite.config.ts`：
  - 开发时代理 `/api` 请求到 Django `localhost:8000`
  - 构建输出到 `frontend/dist/`
- 验证 `pnpm dev` 能启动 Vue 开发服务器
- 验证 Vue 页面能通过代理访问 `/api/health/`

**验收标准：**
- [x] `pnpm dev` 启动 Vite 开发服务器
- [x] 浏览器访问 `localhost:5173` 看到 Vue 页面
- [x] API 代理工作正常

**git commit:** `feat(frontend): Initialize Vue 3 + TypeScript + Vite project`

---

### Step 0.4：配置 Obsidian Vault 路径

**详细操作：**
- 在 `backend/.env` 中新增：
  ```
  SYNAPSE_PM_BACKEND='vault'
  OBSIDIAN_VAULT_PATH='/home/james/syncthing/ObsidianVault/PARA-Vault'
  ```
- 在 `settings.py` 中读取并验证路径

**验收标准：**
- [x] Django 启动时检查 vault 路径是否存在
- [x] 路径不存在时给出明确警告（不阻塞启动）

**git commit:** `feat(config): Add Obsidian vault path and PM backend configuration`

---

## Phase 1：Vue 前端骨架 + API 基础

**目标：** 搭建完整的 Vue 应用骨架——布局、路由、状态管理。后端提供基础 API。

---

### Step 1.1：创建 Vue 应用骨架 — Layout 和 Router

**详细操作：**
- `AppLayout.vue`: 侧边栏 + 顶部导航 + 主内容区
- `Sidebar.vue`: 导航菜单（Dashboard / PM / Attendance / BOM）
- `Header.vue`: 标题 + 用户信息 + 语言切换
- Vue Router 配置：
  ```typescript
  const routes = [
    { path: '/', component: Dashboard },
    { path: '/pm', component: PMLayout, children: [
      { path: 'projects', component: ProjectList },
      { path: 'gantt', component: GanttView },
    ]},
    { path: '/attendance', component: AttendanceLayout },
    { path: '/bom', component: BOMLayout },
  ]
  ```
- 所有页面先用占位内容

**验收标准：**
- [x] 侧边栏导航可点击切换页面
- [x] 页面之间无刷新切换（SPA）
- [x] 响应式布局（移动端侧边栏收起）

**git commit:** `feat(frontend): Add app layout, sidebar navigation, and router`

---

### Step 1.2：Pinia Store 初始化 + API 通信层

**详细操作：**
- `api/client.ts`: Axios 实例配置（baseURL、拦截器、错误处理）
- `stores/app.ts`: 全局状态（侧边栏状态、语言、PM 后端模式）
- `stores/auth.ts`: 认证状态（先用 session，预留 JWT）
- `types/api.ts`: API 响应类型定义

**验收标准：**
- [x] API 调用统一通过 `api/client.ts`
- [x] 网络错误有统一的 toast 提示
- [x] TypeScript 类型完整

**git commit:** `feat(frontend): Add Pinia stores and Axios API client`

---

### Step 1.3：Dashboard 首页 Vue 化

**详细操作：**
- 后端：`GET /api/dashboard/` → 返回通知内容 + 模块列表
- 前端：`Dashboard.vue` — 显示通知面板 + 工具卡片
- Markdown 渲染：使用 `markdown-it` 库（前端渲染）

**验收标准：**
- [x] Dashboard 显示与旧版相同的信息
- [x] 工具卡片点击可导航到对应页面

**git commit:** `feat(dashboard): Migrate dashboard to Vue with API backend`

---

## Phase 2：PM 核心 — Obsidian 读取 + 展示

**目标：** 从 Obsidian vault 读取项目/任务数据，在 Vue 前端展示。

---

### Step 2.1：创建 synapse_pm Django App

**详细操作：**
- `python manage.py startapp synapse_pm`（在 `backend/src/` 下）
- 注册到 `INSTALLED_APPS` 和 `SYNAPSE_MODULES`
- 基本 URL 路由 `/api/pm/`
- Django Models（用于缓存和 database 模式）：
  ```python
  class Project(models.Model):
      name, para_type, vault_path, status, created, deadline, ...

  class Task(models.Model):
      uuid, name, project(FK), status, priority, created, deadline,
      estimated_hours, depends_on(M2M self), vault_path, ...

  class TimeEntry(models.Model):
      task(FK), date, description, start_time, end_time, duration, ...
  ```

**验收标准：**
- [x] `python manage.py migrate` 成功
- [x] Django admin 中可以看到 PM 模型

**git commit:** `feat(pm): Create synapse_pm app with data models`

---

### Step 2.2：实现 Backend Adapter 抽象层

**详细操作：**
- `adapters/base.py`: `PMBackendAdapter` 抽象基类
- `adapters/vault_adapter.py`: `VaultAdapter` — 从 .md 文件读写
- `adapters/db_adapter.py`: `DatabaseAdapter` — 从数据库读写
- `adapters/__init__.py`: 工厂函数，根据 `settings.SYNAPSE_PM_BACKEND` 返回正确的 adapter

**验收标准：**
- [x] `get_adapter()` 根据配置返回正确的 adapter
- [x] 两个 adapter 实现相同接口

**git commit:** `de6ca5e feat(pm): Implement Backend Adapter pattern for PM data access`

---

### Step 2.3：实现 VaultAdapter — 读取 Obsidian 数据

**详细操作：**
- `vault/reader.py`:
  - `scan_projects()`: 扫描 `1_PROJECT/` 和 `4_ARCHIVE/`
  - `scan_tasks(project_path)`: 扫描 `tasks/` 子目录
  - `parse_task_file(file_path)`: 解析 YAML frontmatter
  - `parse_daily_note_time_blocks(file_path)`: 正则解析时间块
  - `aggregate_time_entries(task_uuid)`: 聚合某任务的所有工时
  - `get_daily_note_path(target_date)`: 推算 daily note 路径
- `vault/writer.py`:
  - `create_task_file(data)`: 生成新 task_xxx.md
  - `update_task_frontmatter(path, updates)`: 原子更新 frontmatter
  - `append_time_block(date, entry)`: 追加时间块到 daily note
- 注：真实 vault 的边缘情况验证在 Step 2.4 `sync_vault` 实际运行时进行

**验收标准：**
- [x] 能正确扫描出所有 project 目录
- [x] 能正确解析 task frontmatter
- [x] 能正确解析 daily note 时间块（单元测试通过）
- [ ] 真实 vault 运行验证（待 Step 2.4 运行后确认）

**git commit:** `8434066 feat(pm): Implement VaultReader and VaultWriter for Obsidian vault parsing`

---

### Step 2.4：实现 SQLite 缓存同步

**详细操作：**
- 新增 `SyncMeta` 模型（key-value，存储 `last_sync_at` 等元数据）
- Management command: `python manage.py sync_vault`
  - `--full`: 忽略 mtime 缓存，强制全量重解析
  - `--dry-run`: 仅报告变化，不写入数据库
- 逻辑：扫描 vault → 对比 SQLite 缓存（按 vault_mtime）→ 增量更新
- 二次 pass 解析 task depends_on M2M 关系
- 自动聚合最近 2 个月的 daily note 时间块

**验收标准：**
- [x] `sync_vault` 命令成功执行（database 模式下优雅退出）
- [x] 增量同步：第二次运行相同 vault，skipped 计数正确
- [x] `SyncMeta.last_sync_at` 在每次成功同步后更新
- [ ] 真实 vault 运行：`./synapse dev:migrate && python manage.py sync_vault --dry-run`

**git commit:** 本次提交

---

### Step 2.5：DRF API — PM 数据接口

**详细操作：**
- `serializers.py`: ProjectSerializer, ProjectDetailSerializer, TaskSerializer,
  TaskWriteSerializer, TimeEntrySerializer, TimeEntryCreateSerializer, GanttTaskSerializer
- `api/views.py`: 函数式 views（@api_view 装饰器）
  - `GET /api/pm/projects/` — 项目列表（支持 status/search/ordering/pagination）
  - `GET /api/pm/projects/{id}/` — 项目详情（含任务列表）
  - `GET/POST /api/pm/tasks/` — 任务列表 + 创建
  - `GET/PATCH /api/pm/tasks/{uuid}/` — 任务详情 + 更新
  - `GET/POST /api/pm/time-entries/` — 时间记录列表 + 新增
  - `GET /api/pm/stats/` — 统计数据
  - `GET /api/pm/gantt/` — 甘特图数据
  - `POST /api/pm/sync/` — 触发 vault 同步（vault 模式）
- `api/urls.py`: 完整 URL 路由注册
- 所有接口通过 adapter 自动选择数据源

**验收标准：**
- [x] 所有 URL 正确解析
- [x] Adapter 方法在 database 模式下正常返回数据
- [ ] 集成测试（真实 HTTP 请求）— 待 Vue 前端联调时验证

**git commit:** 本次提交

---

### Step 2.6：Vue 前端 — 项目列表和任务视图

**详细操作：**
- `types/pm.ts`: Project, Task, TimeEntry, GanttTask, PmStats 类型定义
- `api/pm.ts`: pmApi 模块（listProjects, getProject, listTasks, getTask, etc.）
- `stores/pm.ts`: usePmStore（projects/tasks/selectedTask/stats/syncing state）
- `stores/app.ts`: 补充 fetchHealth()，从 /api/health/ 读取 pmBackend
- `views/pm/PmIndex.vue`: 路由入口，根据 ?project= query 切换两个视图
- `views/pm/ProjectList.vue`: 项目列表，DataTable + 状态过滤 + stats bar + sync 按钮
- `views/pm/ProjectTaskView.vue`: 项目内任务列表，支持 status/priority/search 过滤
- `views/pm/TaskDetail.vue`: 任务详情 Drawer（meta + 时间记录表 + vault 信息）
- `backend/synapse_api/views.py`: health_check 补充 pm_backend/vault_connected 字段

**验收标准：**
- [x] vue-tsc + vite build 零错误
- [x] /api/health/ 返回 pm_backend 字段
- [ ] 端到端联调（需要运行 ./synapse run + ./synapse frontend:run）

**git commit:** 本次提交

---

## Phase 3：PM 进阶 — 甘特图 + 写回 Obsidian

**目标：** 可视化甘特图 + 双向数据流（Synapse → Obsidian）。

---

### Step 3.1：集成 frappe-gantt

**详细操作：**
- `pnpm install frappe-gantt`
- `components/pm/GanttChart.vue`: frappe-gantt 的 Vue 封装组件
- `views/pm/GanttView.vue`: 甘特图页面
  - 从 API 获取数据
  - 渲染甘特图
  - 支持视图切换（日/周/月）
  - 支持项目筛选

**验收标准：**
- [x] 甘特图正确渲染任务时间线
- [x] 任务之间的依赖关系以箭头显示
- [x] 可以切换视图（日/周/月）

**git commit:** `feat(pm): Integrate frappe-gantt chart view`

---

### Step 3.2：甘特图交互 — 拖拽修改

**详细操作：**
- 拖拽调整任务时间 → 触发 API 更新
- 点击任务 → 弹出详情侧边栏
- 双击任务 → 进入编辑模式
- 进度条显示完成度

**验收标准：**
- [x] 拖拽修改时间后，数据写入后端
- [x] 刷新页面后数据保持一致

**git commit:** `feat(pm): Add Gantt chart drag-and-drop interactions`

---

### Step 3.3：实现 VaultWriter — 写入 Obsidian

**详细操作：**
- `vault/writer.py`:
  - `create_task_file()`: 生成新 task_xxx.md
  - `update_task_frontmatter()`: 更新 task 的 YAML frontmatter
  - `append_time_block()`: 追加时间块到 daily note
  - `create_daily_note()`: 按模板创建新的 daily note
- 原子写入策略
- 格式严格遵循用户现有的 Obsidian 模板

**验收标准：**
- [x] 创建的 task 文件在 Obsidian 中正确显示
- [x] 更新的 frontmatter 不破坏其他内容
- [x] 追加的时间块被 Dataview 脚本正确识别
- [x] 写入后 Syncthing 正常同步

**git commit:** `feat(pm): Implement VaultWriter for Obsidian vault write-back`

---

### Step 3.4：写入 API 接口

**详细操作：**
- `POST /api/pm/tasks/` → 创建任务 → VaultWriter.create_task_file()
- `PATCH /api/pm/tasks/{uuid}/` → 更新任务 → VaultWriter.update_task_frontmatter()
- `POST /api/pm/time-entries/` → 记录时间 → VaultWriter.append_time_block()

**验收标准：**
- [x] 从 Synapse 创建的任务在 Obsidian 中立即可见
- [x] 从 Synapse 记录的时间在当天 daily note 中出现

**git commit:** `feat(pm): Add write API endpoints with VaultWriter integration`

---

## Phase 4：迁移现有模块到 Vue

**目标：** 将 Attendance 和 BOM 分析器迁移到 Vue SPA。

---

### Step 4.1：Attendance Analyzer API + Vue 页面

**详细操作：**
- 后端：将现有的 `AnalysisView` 改为 DRF API
  - `POST /api/attendance/analyze/` — 上传文件 + 分析
  - `GET /api/attendance/download/` — 下载报告
- 前端：`views/attendance/Upload.vue` + `Result.vue`

**git commit:** `feat(attendance): Migrate to Vue frontend with DRF API`

---

### Step 4.2：BOM Analyzer API + Vue 页面

**详细操作：**
- 后端：将现有的 `analysis_view` 改为 DRF API
  - `POST /api/bom/analyze/` — 上传文件 + 分析
  - `GET /api/bom/download/` — 下载报告
- 前端：`views/bom/Upload.vue` + `Result.vue`

**git commit:** `feat(bom): Migrate to Vue frontend with DRF API`

---

### Step 4.3：移除 Django Templates

**详细操作：**
- 确认所有页面都已 Vue 化
- 删除 `templates/` 目录
- 删除 Django 视图中的 `render()` 调用
- 更新 Nginx 配置：static 指向 Vue build 输出

**git commit:** `refactor: Remove Django templates after full Vue migration`

---

## Phase 5：Docker 容器化

**目标：** `docker-compose up` 一键启动。

---

### Step 5.1：Dockerfile

```dockerfile
# docker/Dockerfile.backend
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
RUN python manage.py collectstatic --noinput
CMD ["gunicorn", "synapse_project.wsgi:application", "--bind", "0.0.0.0:8000"]

# docker/Dockerfile.frontend
FROM node:18-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install
COPY frontend/ .
RUN pnpm build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
```

**git commit:** `feat(docker): Add Dockerfiles for backend and frontend`

---

### Step 5.2：docker-compose.yml

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    env_file: backend/.env
    volumes:
      - ${OBSIDIAN_VAULT_PATH:-./data}:/mnt/obsidian:rw  # Obsidian vault mount
      - db_data:/app/data
    ports:
      - "8000:8000"

  frontend:
    build:
      context: .
      dockerfile: docker/Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  db_data:
```

**git commit:** `feat(docker): Add docker-compose configuration`

---

### Step 5.3：文档和脚本

- `README.md` 更新 Docker 部署说明
- `run.sh` 添加 `docker:up` / `docker:down` / `docker:build` 命令

**git commit:** `docs(docker): Add Docker deployment documentation`

---

## Phase 6：持续扩展（长期路线图）

| 序号 | 模块 | 描述 | 前置条件 |
|------|------|------|----------|
| 6.1 | 周报/月报生成器 | 从 daily notes 聚合生成报告 | Phase 2 完成 |
| 6.2 | 全文搜索 | 搜索 Obsidian vault 所有内容 | Phase 2 完成 |
| 6.3 | 认证系统 (JWT) | 支持多用户 + API Token | Phase 1 完成 |
| 6.4 | 实时更新 (WebSocket) | 甘特图实时协作 | Phase 3 完成 |
| 6.5 | 移动端适配 | 响应式 + PWA | Phase 4 完成 |
| 6.6 | 审批流 | 简单的审批链 | Phase 3 完成 |
| 6.7 | 数据看板 | ECharts 统计仪表盘 | Phase 2 完成 |

---

## 执行纪律（重申）

```
每一个 Step：
1. 明确目标（本文档中的验收标准）
2. 编码实现（注释详细、TypeScript 类型完整）
3. 测试验证（手动 + 自动）
4. git commit（有意义的 conventional commit message）
5. 确认不影响现有功能
6. 进入下一步

绝不跳步。绝不在未 commit 的情况下开始下一步。
```
