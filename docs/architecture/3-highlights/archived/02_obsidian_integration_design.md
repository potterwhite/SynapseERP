# Obsidian 融合方案详细设计

> 评估日期：2026-03-21
> 状态：方案草案，待确认

---

## 一、核心理念

**Synapse 不替代 Obsidian，而是成为 Obsidian 的「高级前端」。**

两者的角色定位：

| 角色 | Obsidian | Synapse |
|------|----------|---------|
| 定位 | 个人知识编辑器 | 数据可视化 + 工作流引擎 |
| 数据所有权 | ✅ 拥有所有 .md 文件 | ❌ 不持有数据，只读写 vault |
| 编辑体验 | ✅ 最佳（所见即所得） | ⚠️ 结构化表单（非自由编辑） |
| 可视化 | ⚠️ 有限（Dataview 表格） | ✅ 甘特图、日历、仪表盘 |
| 批量操作 | ❌ 手动 | ✅ 自动化（写入 daily note 等） |
| 离线能力 | ✅ 完全离线 | ⚠️ 需要服务运行 |

---

## 二、数据模型映射

### 2.1 你的 PARA 层级 → Synapse 数据模型

```
Obsidian Vault                      Synapse Model
──────────────                      ──────────────
2_AREA/                             Area
├── 01-Area-Journal                 ├── Area(name="Journal")
├── 03-Area-Career                  ├── Area(name="Career")
└── 05-Area-Job-Baytto              └── Area(name="Job-Baytto")

1_PROJECT/                          Project (belongs_to Area)
├── 2025.19_Project_Synapse         ├── Project(name="Synapse", area="Career")
└── 2025.7_Project_Offline_ASR      └── Project(name="Offline_ASR", area="Career")

1_PROJECT/*/tasks/                  Task (belongs_to Project)
└── task_xxx.md                     └── Task(uuid="xxx", project="Synapse")

2_AREA/01-Area-Journal/2026/Daily/  DailyNote
└── March 21, 2026.md               └── DailyNote(date=2026-03-21)
```

### 2.2 Markdown Frontmatter → ORM Model

你现有的 task 文件 frontmatter：
```yaml
---
task_uuid: 693d3007-e356-418f-9863-5d8a3fe38b89
task_name: task_打算扩建synapse_自建一个做PM
project:
  - "[[2025.19_Project_Synapse]]"
created: 2026-03-21
status: todo
priority: medium
tags: journal/task
---
```

Synapse 解析后的内存表示：
```python
class VaultTask:
    uuid: str           # task_uuid
    name: str           # task_name
    project_ref: str    # 从 wikilink 提取 "2025.19_Project_Synapse"
    created: date
    status: str         # todo | doing | done | cancelled
    priority: str       # low | medium | high
    # 以下从 daily notes 的时间块聚合而来
    time_entries: List[TimeEntry]
    total_minutes: int
```

### 2.3 Daily Note 时间块 → TimeEntry

你的时间块格式：
```markdown
- [ ] 任务描述 (start:: 08:10) (end:: 10:00) (task_uuid:: xxx) (task_name:: [[task_xxx]])
```

Synapse 解析：
```python
class TimeEntry:
    date: date          # 从文件名 "March 21, 2026" 解析
    description: str    # "任务描述"
    start: time         # 08:10
    end: time           # 10:00
    task_uuid: str      # 关联 task
    duration_minutes: int  # 自动计算
```

---

## 三、读写策略

### 3.1 读取 — VaultReader

```
VaultReader
├── scan_areas()         # 扫描 2_AREA/ 目录结构
├── scan_projects()      # 扫描 1_PROJECT/ 目录结构
├── scan_tasks()         # 扫描所有 tasks/ 目录下的 task_*.md
├── scan_daily_notes()   # 扫描 Daily/ 目录
├── parse_frontmatter()  # 解析 YAML frontmatter
└── parse_time_blocks()  # 用正则解析时间块
```

**缓存策略：**
- 文件的 `mtime`（最后修改时间）作为缓存失效依据
- 不需要 watch 文件系统变化（每次请求时检查 mtime 即可）
- 未来可以加 `inotify` 做实时监听

### 3.2 写入 — VaultWriter

**写入场景：**

1. **从甘特图创建新任务 → 生成 task_xxx.md**
2. **从甘特图记录时间 → 追加到当天 daily note 的时间块**
3. **更新任务状态 → 修改 task_xxx.md 的 frontmatter**

**写入安全策略：**

```python
class VaultWriter:
    def write_task(self, task: VaultTask):
        """写入或更新 task 文件"""
        # 1. 构建 YAML frontmatter + markdown body
        # 2. 使用 tempfile 写入临时文件
        # 3. os.rename() 原子替换（同一文件系统内是原子操作）

    def append_time_block(self, date: date, entry: TimeEntry):
        """追加时间块到 daily note"""
        # 1. 读取整个 daily note
        # 2. 找到 "⏳ 时间块记录" section
        # 3. 在该 section 末尾追加新行
        # 4. 原子写回
```

**与 Obsidian 共存的关键原则：**
1. **永远不删除用户手动编写的内容**
2. **只在明确的标记区域内操作**（如时间块 section）
3. **遵循用户现有的格式约定**（YAML frontmatter 字段名不变）
4. **写入时使用原子操作，避免 Syncthing 同步半写文件**

---

## 四、不存储到数据库的 "Zero-DB" 方案 vs 混合方案

### 方案 A：Zero-DB（纯文件系统）

```
Synapse ←→ Obsidian Vault (唯一数据源)
```

- ✅ 数据零冗余
- ✅ Obsidian 中即时可见
- ❌ 每次都要扫描文件系统，性能随文件数增长
- ❌ 查询能力受限（无 SQL）

### 方案 B：混合方案（文件系统 + SQLite 缓存）

```
Synapse ←→ SQLite Cache ←→ Obsidian Vault (真实数据源)
              ↑ 启动时/周期性同步
```

- ✅ 查询快速（SQL）
- ✅ 支持复杂过滤/排序
- ✅ 首次扫描后极快
- ⚠️ 需要同步机制
- ✅ Obsidian 中仍可见所有数据

### 推荐：方案 B — 混合方案

**理由：** 你的 vault 有 592 个目录，文件数量级可能在数千。纯文件扫描每次请求都做的话太慢。SQLite 缓存 + mtime 比对是最佳平衡。

---

## 五、甘特图需要的数据字段

为了让甘特图工作，每个任务需要以下信息：

| 字段 | 来源 | 是否已有 |
|------|------|----------|
| task_uuid | frontmatter | ✅ |
| task_name | frontmatter | ✅ |
| project | frontmatter | ✅ |
| status | frontmatter | ✅ |
| priority | frontmatter | ✅ |
| created | frontmatter | ✅ |
| **deadline** | frontmatter | ❌ 需要新增 |
| **estimated_hours** | frontmatter | ❌ 需要新增 |
| **depends_on** | frontmatter | ❌ 需要新增（任务间依赖） |
| **area** | 目录结构推断 | ✅ 可从路径提取 |
| actual_hours | daily note 时间块聚合 | ✅ |

**需要你确认的扩展 frontmatter 格式：**

```yaml
---
task_uuid: 693d3007-e356-418f-9863-5d8a3fe38b89
task_name: task_xxx
project:
  - "[[2025.19_Project_Synapse]]"
created: 2026-03-21
deadline: 2026-04-15            # 新增
estimated_hours: 8              # 新增
depends_on:                     # 新增
  - "uuid-of-blocking-task"
status: todo
priority: medium
tags: journal/task
---
```

---

## 六、与 Obsidian 的兼容性保证

| 操作 | 兼容性 |
|------|--------|
| Synapse 添加的 frontmatter 字段 | ✅ Obsidian 会忽略不认识的字段 |
| Synapse 写入的时间块格式 | ✅ 你的 Dataview 脚本已经能解析 |
| Synapse 创建的新 task 文件 | ✅ 遵循你的命名和模板格式 |
| Synapse 创建的 daily note | ✅ 遵循你的 Templater 模板结构 |
| 图表 PNG 嵌入 | ✅ 用 `![[exports/gantt_2026-03-21.png]]` |

**结论：100% 兼容。两者操作同一批文件，互不破坏。**
