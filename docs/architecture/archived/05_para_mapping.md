# PARA 映射关系重新理解

> 日期：2026-03-21
> 状态：已更正

---

## 一、对 PARA 体系的正确理解

用户的 PARA 体系遵循 Tiago Forte 的定义：

| 层级 | 含义 | 特征 | 对应 vault 目录 |
|------|------|------|----------------|
| **Project** | 有明确时间边界的目标 | 有开始/结束，可完成 | `1_PROJECT/` |
| **Area** | 持续维护的责任领域 | 无明确结束时间 | `2_AREA/` |
| **Resource** | 参考资料/知识库 | 被动引用 | `3_RESOURCE/` |
| **Archive** | 已完成/搁置的项目 | 冷存储 | `4_ARCHIVE/` |

### 关键纠正

**Area 下的 "Project_xxx" 不是顶层 Project！**

```
2_AREA/
├── 01-Area-Journal           ← 这是一个 Area（持续的日志习惯）
│   ├── Project_Obsidian-Nexus ← 这是 Area 下的一个子项目（可以理解为 Initiative）
│   └── Project_TODO           ← 这也是子项目
├── 03-Area-Career            ← 这是一个 Area（职业发展，永不结束）
│   ├── Project_Career         ← Area 下的子项目（求职相关）
│   └── Project_GitHubPage     ← Area 下的子项目
```

**而 1_PROJECT/ 下的才是真正的顶层 Project：**

```
1_PROJECT/
├── 2025.19_Project_Synapse       ← 真正的 Project（有时间边界）
├── 2025.7_Project_Offline_ASR    ← 真正的 Project
└── 2026.03_Project_自建机场       ← 真正的 Project
```

### 映射规则

```
Obsidian Vault              →    Synapse Data Model
─────────────                    ──────────────────
1_PROJECT/xxx               →    Project(type="bounded", source="1_PROJECT")
2_AREA/xx-Area-Name         →    Category(type="ongoing")  # 不叫 Area，避免 PARA 术语泄露
2_AREA/.../Project_xxx      →    Sub-initiative under Category  # 可选：也视为 Project
4_ARCHIVE/xxx               →    Project(type="bounded", archived=True)
```

---

## 二、显示层与数据层的分离

**原则：PARA 是内部映射逻辑，用户（尤其是团队成员）看到的是通用的项目管理界面。**

### 用户界面看到的

```
┌─────────────────────────────────┐
│  Synapse Project Management     │
├─────────────────────────────────┤
│  📁 Projects                    │
│  ├── Synapse Framework [进行中]  │
│  ├── Offline ASR [进行中]        │
│  ├── PCIe CaptureCard [进行中]   │
│  └── 自建机场 [进行中]            │
│                                  │
│  📁 Archived                     │
│  ├── Project Alpha [已完成]      │
│  └── QEMU Training [已完成]      │
│                                  │
│  📁 Ongoing Areas (可选/个人)     │
│  ├── Career                      │
│  └── Families                    │
└─────────────────────────────────┘
```

### 底层数据层知道的

```python
# Synapse 内部知道每个 Project 的来源
project.vault_path = "1_PROJECT/2025.19_Project_Synapse"
project.para_type = "project"  # 内部标记

category.vault_path = "2_AREA/03-Area-Career"
category.para_type = "area"    # 内部标记
```

---

## 三、团队使用时的考量

当 Synapse 给团队使用时：
- **不需要暴露 PARA 概念**
- 团队成员只看到：Projects → Tasks → Gantt Chart
- Areas 可以作为"分类"或"部门"存在，但命名不使用 PARA 术语
- **Area 下的子 Project** 可以扁平化为普通 Project（加一个 category 标签）

---

## 四、数据存储的双轨制问题

**矛盾点：**
- 个人模式：数据在 Obsidian vault（.md 文件）
- 团队模式：团队成员没有 Obsidian，数据必须在数据库

**解决方案：**

```
数据抽象层 (Data Abstraction Layer)
├── VaultBackend     → 读写 Obsidian .md 文件 (个人模式)
├── DatabaseBackend  → 读写 PostgreSQL/SQLite (团队模式)
└── SyncBridge       → 双向同步 Vault ↔ Database (混合模式)
```

这样 Synapse 的业务逻辑只跟抽象层交互，不关心底层是文件还是数据库。

个人模式可以先只做 VaultBackend，团队模式时再加 DatabaseBackend + SyncBridge。
