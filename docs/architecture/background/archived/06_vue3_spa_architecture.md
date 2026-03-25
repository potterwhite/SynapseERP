# Vue 3 SPA 架构方案

> 日期：2026-03-21
> 状态：基于用户选择 "Vue 3 SPA" 的详细方案

---

## 一、选择 Vue 3 SPA 的架构影响

### 整体架构变化

**从：**
```
Client (Browser) → Django Templates (SSR) → Django Views → Database
```

**变为：**
```
┌─────────────────────┐     ┌──────────────────────────┐
│  Vue 3 SPA (前端)    │     │  Django DRF API (后端)    │
│  - Vite 构建         │────→│  - REST API endpoints    │
│  - Vue Router        │←────│  - VaultReader/Writer    │
│  - Pinia 状态管理    │     │  - Auth (JWT/Session)    │
│  - UI 组件库         │     │  - SQLite/PostgreSQL     │
│  - 甘特图/日历       │     │  - Obsidian Vault I/O    │
└─────────────────────┘     └──────────────────────────┘
      Nginx (static)              Gunicorn (API)
```

### 关键决策树

```
Vue 3 SPA
├── 构建工具: Vite (最快，Vue 官方推荐)
├── 路由: Vue Router 4
├── 状态管理: Pinia
├── UI 框架: ???  ← 需要决定
├── 甘特图: ???   ← 需要决定
├── HTTP 客户端: Axios / fetch
├── 类型系统: TypeScript (推荐) / JavaScript
└── CSS 方案: ???  ← 需要决定
```

---

## 二、前端仓库结构

### 方案 A：Monorepo（前后端同一仓库）

```
SynapseERP.git/
├── backend/                    # Django 后端 (原有代码移入)
│   ├── src/
│   ├── synapse_project/
│   ├── manage.py
│   └── requirements.txt
├── frontend/                   # Vue 3 前端 (新增)
│   ├── src/
│   │   ├── views/
│   │   ├── components/
│   │   ├── stores/
│   │   ├── api/
│   │   └── router/
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
└── docs/
```

### 方案 B：保持现有结构，前端在子目录

```
SynapseERP.git/                 # 结构不变
├── src/                        # Django apps (不动)
├── synapse_project/            # Django config (不动)
├── frontend/                   # Vue 3 前端 (新增)
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── manage.py
└── requirements.txt
```

**推荐方案 B** — 改动最小，不需要重组现有代码。

---

## 三、Vue 3 前端 UI 框架选型

| 框架 | 特点 | Star | 文档中文化 | 推荐度 |
|------|------|------|-----------|--------|
| **Element Plus** | 企业级，最全组件库 | 25k+ | ✅ 原生中文 | ⭐⭐⭐⭐⭐ |
| **Naive UI** | 性能优秀，TypeScript | 16k+ | ✅ 中文 | ⭐⭐⭐⭐ |
| **Ant Design Vue** | 蚂蚁设计体系 | 20k+ | ✅ 中文 | ⭐⭐⭐⭐ |
| **Vuetify 3** | Material Design | 40k+ | ⚠️ 英文为主 | ⭐⭐⭐ |
| **PrimeVue** | 丰富主题 | 10k+ | ❌ 英文 | ⭐⭐⭐ |
| **Headless UI** | 无样式，完全自定义 | 25k+ | ❌ 英文 | ⭐⭐ |

**推荐 Element Plus** — 原因：
1. 中文文档最完善（降低你的学习曲线）
2. 表格/表单/日期选择器/树形组件一应俱全
3. 与企业级管理系统场景完美匹配
4. 社区最活跃，问题最容易搜到答案

---

## 四、甘特图库选型（Vue 3 生态）

| 库 | Vue 3 支持 | 免费 | 交互级别 | 推荐度 |
|---|-----------|-----|---------|--------|
| **DHTMLX Gantt** | ✅ (wrapper) | ⚠️ 免费版有限 | 🟢🟢🟢 最强 | ⭐⭐⭐⭐ |
| **frappe-gantt** | ✅ (需封装) | ✅ MIT | 🟢🟢 中等 | ⭐⭐⭐⭐ |
| **@neolution/vue-gantt** | ✅ 原生 | ✅ | 🟡 基础 | ⭐⭐⭐ |
| **Apache ECharts** | ✅ (vue-echarts) | ✅ | 🟢 良好 | ⭐⭐⭐ |
| **Bryntum Gantt** | ✅ | ❌ 付费 | 🟢🟢🟢 最强 | ⭐⭐⭐⭐⭐(付费) |
| **自绘 (D3.js/Canvas)** | ✅ | ✅ | 🟢🟢🟢 完全可控 | ⭐⭐(工作量大) |

**两条推荐路线：**

1. **快速路线：frappe-gantt + Vue wrapper**
   - 2-3 天可以出甘特图
   - 功能足够（拖拽、依赖线、多视图）
   - 后续可替换

2. **企业路线：DHTMLX Gantt (GPL 版)**
   - 免费版支持基本甘特图
   - 功能最全（资源视图、关键路径、导入导出）
   - 但免费版不支持树形结构和分组

---

## 五、Vue 3 SPA 带来的额外工作量

**相比 HTMX 路线多出的工作：**

| 工作项 | 估时 | 说明 |
|--------|------|------|
| 搭建 Vite + Vue 3 项目 | 0.5 天 | create-vite |
| 配置 Vue Router | 0.5 天 | 路由定义 |
| 配置 Pinia stores | 1 天 | 状态管理 |
| Element Plus 集成 | 0.5 天 | 按需导入 |
| API 通信层 (Axios) | 1 天 | 统一拦截器/错误处理 |
| 认证机制 (JWT/Session) | 1-2 天 | 登录页/Token刷新 |
| Layout 框架 | 1 天 | 侧边栏/Header/Breadcrumb |
| DRF API 完整实现 | 2-3 天 | CRUD + 序列化 |
| **总计额外工作** | **~7-10 天** | 相比 HTMX 路线 |

**但获得的优势：**
- 更流畅的用户体验（SPA 无页面刷新）
- 更强大的交互能力（拖拽、实时更新、动画）
- 前后端解耦（API 可被移动端/其他客户端复用）
- 团队模式时更容易扩展

---

## 六、是否使用 TypeScript？

| 方案 | 优点 | 缺点 |
|------|------|------|
| **TypeScript** | 类型安全、IDE 提示、重构安全 | 学习成本、配置成本 |
| **JavaScript** | 上手快、无额外配置 | 大项目维护困难 |

**推荐 TypeScript** — 你的项目是长期项目，类型系统的投资会很快回本。但如果你对 TypeScript 完全陌生，可以先用 JS 快速出原型，后续迁移。

---

## 七、开发环境需求

Vue 3 SPA 需要在你的开发机上安装：

```bash
# Node.js (v18+ 推荐)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 验证
node -v  # v18.x
npm -v   # 9.x

# pnpm (推荐替代 npm，更快)
npm install -g pnpm
```

**这是 HTMX 路线不需要的额外依赖** — 你需要确认是否接受。
