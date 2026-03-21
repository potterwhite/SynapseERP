# 前端技术路线决策

> 评估日期：2026-03-21
> 状态：待确认

---

## 一、核心问题

当前 Synapse 是纯 Django 模板渲染（SSR）。要加入甘特图、日历、拖拽等交互式 UI，必须引入前端能力。

问题是：**引入多少前端？**

---

## 二、三条路线对比

### 路线 A：Django Templates + HTMX + Alpine.js（渐进增强）

```
Django Templates (现有)
  + HTMX (声明式 AJAX，无需写 JS)
  + Alpine.js (轻量响应式，17KB)
  + 独立图表库 (frappe-gantt / ECharts)
```

| 维度 | 评价 |
|------|------|
| 学习成本 | 🟢 极低（你已会 Django Templates） |
| 代码改动 | 🟢 渐进式，不需要重写现有代码 |
| 交互能力 | 🟡 中等（够用于甘特图/表单/筛选） |
| 构建系统 | 🟢 不需要（CDN 或 static 引入） |
| 生态丰富度 | 🟡 中等 |
| 适合场景 | 工具型应用、内部系统 |

**示例：HTMX 驱动的甘特图页面**
```html
<!-- 无需写任何 JavaScript fetch 代码 -->
<select hx-get="/pm/api/tasks/" hx-target="#gantt-container"
        hx-trigger="change" name="project">
    <option value="all">All Projects</option>
    <option value="synapse">Synapse</option>
</select>
<div id="gantt-container">
    <!-- HTMX 自动替换此区域 -->
</div>
```

### 路线 B：Django Backend + Vue.js SPA（前后端分离）

```
Django (REST API via DRF)
  + Vue 3 + Vite (SPA)
  + Pinia (状态管理)
  + Vue Router
  + 图表库
```

| 维度 | 评价 |
|------|------|
| 学习成本 | 🔴 高（需要学 Vue + Vite + 构建系统） |
| 代码改动 | 🔴 大（需要重写所有前端） |
| 交互能力 | 🟢 极强（完整 SPA 体验） |
| 构建系统 | 🔴 需要 Node.js + Vite |
| 生态丰富度 | 🟢 极丰富 |
| 适合场景 | 复杂交互应用、需要移动端 |

### 路线 C：混合方案（Django Templates 为主 + 局部 Vue/React 组件）

```
Django Templates (现有页面保留)
  + 甘特图页面用独立 JS 组件
  + DRF API 只为需要的组件提供数据
```

| 维度 | 评价 |
|------|------|
| 学习成本 | 🟡 中（只在需要时写 JS） |
| 代码改动 | 🟡 中（现有代码不动，新功能用新技术） |
| 交互能力 | 🟢 强（局部组件可以很强） |
| 构建系统 | 🟡 可选（简单 JS 不需要，复杂组件需要） |
| 适合场景 | 渐进式演进 |

---

## 三、推荐路线

### 🏆 推荐路线 A（短期）→ 路线 C（中期）

**理由：**

1. **你是嵌入式 Linux 工程师**，不是前端工程师。HTMX + Alpine.js 让你用后端思维写前端。
2. **现有代码零废弃** — 不需要重写 attendance/bom 模块。
3. **甘特图是独立组件** — 用原生 JS 库（frappe-gantt）即可，不需要 Vue/React 包裹。
4. **未来如果需要更复杂的交互**，再在特定页面引入 Vue 组件（路线 C 的渐进方式）。

**具体技术栈：**

```
保留: Django Templates + Gunicorn + Nginx
新增: HTMX 1.9+ (CDN)          → 声明式 AJAX
新增: Alpine.js 3.x (CDN)       → 轻量响应式
新增: frappe-gantt (npm/CDN)     → 甘特图
新增: DRF API (已在依赖中)       → 为甘特图提供 JSON 数据
可选: Tailwind CSS (CDN)         → 替代 inline CSS
```

---

## 四、甘特图技术方案

### 4.1 frappe-gantt 介绍

```
GitHub: frappe/gantt (MIT License)
大小: ~50KB
依赖: 零
特性:
  - 拖拽调整任务时间
  - 任务依赖箭头
  - 日/周/月视图切换
  - 点击任务弹出详情
  - 纯 SVG 渲染
```

### 4.2 数据流

```
Obsidian Vault (.md files)
       ↓ VaultReader (Python)
SQLite Cache (indexed)
       ↓ DRF API (/pm/api/tasks/)
JSON Response
       ↓ JavaScript fetch
frappe-gantt.render(tasks)
       ↓ 用户拖拽/修改
POST /pm/api/tasks/{uuid}/
       ↓ VaultWriter (Python)
Obsidian Vault (.md files updated)
```

### 4.3 甘特图视图层级

```
Level 0: Area 总览
  ├── 01-Area-Journal [████████░░] 80%
  ├── 03-Area-Career  [██████░░░░] 60%
  └── 05-Area-Job     [████░░░░░░] 40%

Level 1: Area → Projects
  Career:
  ├── Project_Synapse    [Mar 1 ─────────── Apr 30]
  ├── Project_Helmsman   [Feb 15 ────── Apr 15]
  └── Project_Offline_ASR [Jan 1 ───────────── Jun 30]

Level 2: Project → Tasks
  Synapse:
  ├── task_setup_framework     [DONE ██████████]
  ├── task_build_bom_analyzer  [DONE ██████████]
  ├── task_build_pm_module     [Mar 21 ─── Apr 15]
  └── task_docker_deployment   [Apr 16 ── Apr 20]
```
