# SynapseERP — Architecture Vision & Competitive Advantage
# SynapseERP — 架构愿景与竞争优势

> Created: 2026-03-25 (Phase 5 planning)
> This document captures the **philosophical and strategic foundations** of SynapseERP.
> 本文档记录 SynapseERP 的**哲学基础与战略定位**。

---

## 1. Core Identity / 核心定位

**SynapseERP is an AI-native, Markdown-first, modular ERP platform.**

**SynapseERP 是一个 AI 原生、Markdown 优先、模块化的 ERP 平台。**

It is designed for the era where:
- AI agents are first-class users of business systems
- Data portability is non-negotiable
- Personal knowledge bases (PKB) and enterprise systems converge
- Lightweight beats bloated; composable beats monolithic

它为以下时代而设计：
- AI 代理是业务系统的一等公民用户
- 数据可移植性不可妥协
- 个人知识库（PKB）与企业系统融合
- 轻量胜过臃肿；可组合胜过单体巨石

---

## 2. Architecture Philosophy / 架构哲学

### 2.1 DB-Primary + Obsidian-Mirror / 数据库为主 + Obsidian 镜像

```
                    ┌─────────────────────┐
                    │   PostgreSQL (DB)    │
                    │   = Source of Truth  │
                    │   = 唯一真相源        │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
     ┌────────────┐   ┌──────────────┐   ┌──────────────┐
     │  Vue SPA   │   │   REST API   │   │  Obsidian    │
     │  (Team)    │   │  (AI Agents) │   │  (You/Admin) │
     │  团队前端   │   │  AI 代理接口  │   │  个人镜像     │
     └────────────┘   └──────────────┘   └──────────────┘
```

**Why this architecture / 为什么这个架构：**

| Aspect | DB-Primary | Obsidian-Primary (rejected) |
|--------|-----------|---------------------------|
| Multi-user concurrency / 多人并发 | ✅ ACID transactions / 事务保护 | ❌ File conflicts / 文件冲突 |
| Permission control / 权限控制 | ✅ Row-level security / 行级安全 | ❌ File-system only / 仅文件系统 |
| AI Agent access / AI 代理访问 | ✅ REST API / 标准接口 | ❌ Must parse .md files / 需解析文件 |
| Query performance / 查询性能 | ✅ Indexed queries / 索引查询 | ❌ Full file scan / 全文件扫描 |
| Your workflow / 你的工作流 | ✅ Obsidian still works as mirror / Obsidian 仍可用 | ✅ Native / 原生 |
| Data portability / 数据可移植 | ✅ Export to Markdown anytime / 随时导出 | ✅ Already Markdown / 本身就是 |

**Key insight / 核心洞察:**

> Obsidian is your **offline IDE** — you can read, edit, and sync back anytime.
> The database is the **coordination layer** — it handles concurrency, permissions, and AI access.
>
> Obsidian 是你的**离线 IDE** — 随时查看、编辑、同步回来。
> 数据库是**协调层** — 它处理并发、权限和 AI 访问。

### 2.2 Markdown-First Data Model / Markdown 优先数据模型

Every model in SynapseERP should be able to:
1. **Export** to a clean, human-readable Markdown file
2. **Import** from a Markdown file with YAML frontmatter
3. **Round-trip** without data loss (DB → MD → DB)

SynapseERP 中每个模型都应该能够：
1. **导出**为干净、人类可读的 Markdown 文件
2. **导入**带 YAML frontmatter 的 Markdown 文件
3. **无损往返**（DB → MD → DB）

This means:
- Your data is never locked in a database
- You can always migrate away
- AI agents can understand your data without a database driver
- Your Obsidian vault is always a valid snapshot of your business state

这意味着：
- 你的数据永远不会被锁在数据库里
- 你可以随时迁移走
- AI 代理无需数据库驱动就能理解你的数据
- 你的 Obsidian vault 始终是业务状态的有效快照

### 2.3 Plugin / Module Architecture / 插件式模块架构

```
synapse_xxx/
├── models.py           # Data layer / 数据层
├── serializers.py      # API contracts / API 契约
├── api/
│   ├── views.py        # REST endpoints / REST 端点
│   └── urls.py         # URL routing / URL 路由
├── adapters/           # Pluggable backends / 可插拔后端
├── vault/              # Obsidian bridge / Obsidian 桥接
├── management/commands/ # CLI tools / 命令行工具
├── migrations/         # Schema evolution / 数据库迁移
└── tests/              # Automated tests / 自动化测试
```

**Adding a new module / 新增模块：**
1. Create `synapse_xxx/` following the template above
2. Register in `INSTALLED_APPS` and `SYNAPSE_MODULES`
3. Include URLs in `api_urls.py`
4. Add Vue views in `frontend/src/views/xxx/`
5. Done — no changes to core needed / 无需修改核心代码

### 2.4 AI-Agent-Ready Design / AI 代理就绪设计

Every API endpoint is designed to be consumed by:
1. Human users (via Vue SPA)
2. AI agents (via REST API directly)
3. CLI tools (via management commands)

每个 API 端点都可以被以下用户使用：
1. 人类用户（通过 Vue SPA）
2. AI 代理（直接调用 REST API）
3. 命令行工具（通过管理命令）

**Future Plugin API design principles / 未来插件 API 设计原则：**

```python
# Every module exposes a standard interface:
# 每个模块暴露标准接口：

class SynapseModule:
    """Base class for all SynapseERP modules"""

    def list_actions(self) -> list[Action]:
        """Return all available actions for AI agent discovery"""

    def execute_action(self, action: str, params: dict) -> Result:
        """Execute a named action — called by AI agents or UI"""

    def export_markdown(self, obj) -> str:
        """Export any object as Markdown"""

    def import_markdown(self, content: str) -> object:
        """Import from Markdown string"""
```

This makes SynapseERP a natural target for:
- **MCP (Model Context Protocol)** servers
- **OpenClaw** / other AI orchestrators
- **Custom AI agents** that manage your business

这让 SynapseERP 天然适配：
- **MCP（模型上下文协议）** 服务器
- **OpenClaw** 等 AI 编排器
- **自定义 AI 代理** 来管理你的业务

---

## 3. Competitive Advantage vs ERPNext / 与 ERPNext 的竞争优势

| Dimension / 维度 | SynapseERP | ERPNext |
|----------|-----------|---------|
| **Architecture era / 架构时代** | 2026 — AI-native / AI 原生 | 2008 — pre-mobile era / 移动前时代 |
| **Frontend / 前端** | Vue 3 + TypeScript + Naive UI | jQuery + custom framework (Frappe) |
| **AI integration / AI 集成** | First-class: Plugin API for agents / 一等公民 | Bolt-on: limited API, no agent design / 后补的 |
| **Data format / 数据格式** | Markdown-first, DB-backed / Markdown 优先 | MariaDB-locked / 锁死在 MariaDB |
| **Obsidian bridge / Obsidian 桥接** | ✅ Unique feature globally / 全球唯一 | ❌ Not possible / 无法实现 |
| **Installation / 安装** | `./synapse prepare` (< 1 min) | bench install (500MB+, 10+ min) |
| **Memory footprint / 内存占用** | ~50MB (Django + Gunicorn) | ~2GB (MariaDB + Redis + Frappe) |
| **Customization / 定制** | Add `synapse_xxx/` module | Learn Frappe Doctypes (steep curve / 学习曲线陡峭) |
| **Data portability / 数据可移植** | Export everything as Markdown / 全部可导出为 Markdown | Locked in Frappe's DocType schema / 锁在 Frappe 模式里 |
| **Community / 社区** | 🌱 Early stage / 早期 | 🌳 Mature (10k+ stars) / 成熟 |

### The killer feature / 杀手级特性

> **No other ERP in the world bridges Obsidian to a team project management system.**
>
> **全世界没有任何 ERP 能将 Obsidian 桥接到团队项目管理系统。**

This means you can:
- Manage your personal knowledge base (PKB) in Obsidian
- Selectively expose project data to your team via SynapseERP
- Let AI agents read/write your business data via REST API
- Never lose a single byte — everything is in Markdown

这意味着你可以：
- 在 Obsidian 中管理你的个人知识库（PKB）
- 通过 SynapseERP 选择性地向团队公开项目数据
- 让 AI 代理通过 REST API 读写你的业务数据
- 永远不丢失一个字节 — 所有数据都在 Markdown 中

---

## 4. Design Principles / 设计原则

1. **Markdown is the universal language / Markdown 是通用语言**
   - Every piece of data can be expressed as Markdown
   - AI agents can read Markdown without special drivers
   - Humans can read Markdown without special tools

2. **API-first, UI-second / API 优先，UI 其次**
   - Every feature is an API endpoint first
   - The Vue SPA is just one client among many
   - AI agents are equally important clients

3. **Modular by default / 默认模块化**
   - Adding a feature = adding a Django app
   - Removing a feature = removing a Django app
   - No core changes needed for either

4. **Lightweight over feature-rich / 轻量胜过功能丰富**
   - Start small, add what you need
   - Don't build features nobody uses
   - Mobile-friendly from day one

5. **Data sovereignty / 数据主权**
   - Your data lives on your servers
   - You can always export everything as files
   - No vendor lock-in, no cloud dependency

6. **AI-agent-welcome / AI 代理友好**
   - Clean, predictable REST API
   - JSON responses with consistent schemas
   - Plugin API for programmatic discovery
   - MCP server compatibility planned

---

## 5. Future Module Roadmap / 未来模块路线图

Based on the current `synapse_xxx` pattern, future modules could include:

基于当前 `synapse_xxx` 模式，未来模块可以包括：

| Module | Purpose / 用途 | Priority / 优先级 |
|--------|----------------|-------------------|
| `synapse_crm` | Customer relationship management / 客户关系管理 | Medium / 中 |
| `synapse_hr` | Human resources / 人力资源 | Low / 低 |
| `synapse_inventory` | Inventory & warehouse / 库存与仓库 | Low / 低 |
| `synapse_finance` | Accounting & invoicing / 会计与发票 | Low / 低 |
| `synapse_docs` | Knowledge base publishing / 知识库发布 | Medium / 中 |
| `synapse_ai` | AI agent orchestration / AI 代理编排 | High / 高 |

Each follows the same pattern:
- `models.py` → `serializers.py` → `api/views.py` → Vue views → Obsidian bridge (optional)

---

## 6. Summary / 总结

SynapseERP is not just another ERP. It is:

SynapseERP 不仅仅是一个 ERP。它是：

> **A personal knowledge bridge between Obsidian and the enterprise,
> designed for the age of AI agents.**
>
> **一座连接 Obsidian 与企业的个人知识桥梁，
> 为 AI 代理时代而设计。**
