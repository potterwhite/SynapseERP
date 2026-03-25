# Obsidian Vault 解析规则精确定义

> 日期：2026-03-21
> 状态：实现规格
> 用途：VaultReader 和 VaultWriter 的精确行为定义

---

## 一、Vault 目录结构规则

### 1.1 项目发现规则

```python
# 扫描 1_PROJECT/ 目录下的直接子目录
# 每个子目录就是一个 Project
VAULT_ROOT = settings.OBSIDIAN_VAULT_PATH

PROJECT_DIR = os.path.join(VAULT_ROOT, "1_PROJECT")
ARCHIVE_DIR = os.path.join(VAULT_ROOT, "4_ARCHIVE", "Completed_Projects")
AREA_DIR = os.path.join(VAULT_ROOT, "2_AREA")

# 项目名称提取规则：
# "2025.19_Project_Synapse" → name="Synapse", full_name="2025.19_Project_Synapse"
# 正则: r'^(\d{4}\.\d+)_Project_(.+)$'
# 如果不匹配正则，full_name 作为 name
PROJECT_NAME_PATTERN = r'^(\d{4}\.\d+)_(?:Project_)?(.+)$'
```

### 1.2 Area 发现规则

```python
# 扫描 2_AREA/ 目录下的直接子目录
# "01-Area-Journal" → name="Journal", order=1
# 正则: r'^(\d+)-Area-(.+)$'
AREA_NAME_PATTERN = r'^(\d+)-Area-(.+)$'
```

### 1.3 Task 发现规则

```python
# 在每个 Project 目录下寻找 tasks/ 子目录
# tasks/ 下的所有 .md 文件都是候选，通过 frontmatter 中的 task_uuid 字段判断是否为 task
# 有 task_uuid 字段 → 是 task；没有 → 跳过
# 跳过 Syncthing 冲突副本（*.sync-conflict-*.md）
# 例: 1_PROJECT/2025.19_Project_Synapse/tasks/task_xxx.md          ← task_ prefix (legacy)
# 例: 1_PROJECT/2025.23_Project_PCIe_CaptureCard/tasks/01-01-02_uart内部信号观测.md ← no prefix, still valid
SYNC_CONFLICT_PATTERN = r'\.sync-conflict-.*\.md$'
# 识别逻辑: read .md → parse frontmatter → has task_uuid? → yes = task
```

### 1.4 Daily Note 发现规则

```python
# Daily notes 路径:
# 2_AREA/01-Area-Journal/{year}/Daily/{month_name}/
# 或 2_AREA/01-Area-Journal/{year}/Daily/
# 文件名格式: "March 21, 2026.md" 或 "2026-03-21.md"

DAILY_NOTE_BASE = os.path.join(AREA_DIR, "01-Area-Journal")

# 文件名日期解析（两种格式）
DATE_FORMAT_1 = "%B %d, %Y"     # "March 21, 2026"
DATE_FORMAT_2 = "%Y-%m-%d"       # "2026-03-21"

# 当天 daily note 路径推算:
# 2026-03-21 → 2_AREA/01-Area-Journal/2026/Daily/March 21, 2026.md
# 注意：3月份的 daily notes 直接在 Daily/ 下，不在 March/ 子目录下
# 而 1月和2月在 January/ 和 February/ 子目录下
# 规则：先检查 Daily/{filename}，再检查 Daily/{MonthName}/{filename}
```

---

## 二、Task 文件 Frontmatter 规格

### 2.1 现有字段（必须兼容）

```yaml
---
task_uuid: 693d3007-e356-418f-9863-5d8a3fe38b89     # UUID v4, 唯一标识 (REQUIRED — 没有此字段的 .md 不被视为 task)
task_name: task_打算扩建synapse_自建一个做PM          # 任务名称 (NOT necessarily unique, may duplicate)
project:                                              # 所属项目，Obsidian wikilink 格式 (可为 list 或 string)
  - "[[2025.19_Project_Synapse]]"
created: 2026-03-21                                   # ISO 日期
status: todo                                          # todo | doing | done | cancelled
priority: medium                                      # low | medium | high
tags: journal/task                                    # Obsidian 标签
---
```

### 2.2 新增字段（由 Synapse 添加）

```yaml
---
# ... 现有字段 ...
deadline: 2026-04-15                                  # 新增: ISO 日期，可选
estimated_hours: 40                                   # 新增: 数字，可选
depends_on:                                           # 新增: UUID 列表，可选
  - "uuid-of-blocking-task-1"
  - "uuid-of-blocking-task-2"
---
```

### 2.3 解析规则

```python
import yaml
import re

def parse_task_file(file_path: str) -> dict:
    """Parse a task markdown file and extract frontmatter + body."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract YAML frontmatter between --- markers
    match = re.match(r'^---\n(.*?)\n---\n?(.*)', content, re.DOTALL)
    if not match:
        return None

    frontmatter = yaml.safe_load(match.group(1))
    body = match.group(2)

    # Extract project name from wikilink
    # "[[2025.19_Project_Synapse]]" → "2025.19_Project_Synapse"
    project_ref = None
    if 'project' in frontmatter:
        project_list = frontmatter['project']
        if isinstance(project_list, list) and project_list:
            wikilink = project_list[0]
            link_match = re.search(r'\[\[([^\]]+)\]\]', str(wikilink))
            if link_match:
                project_ref = link_match.group(1)

    return {
        'uuid': frontmatter.get('task_uuid'),
        'name': frontmatter.get('task_name'),
        'project_ref': project_ref,
        'created': frontmatter.get('created'),
        'status': frontmatter.get('status', 'todo'),
        'priority': frontmatter.get('priority', 'medium'),
        'deadline': frontmatter.get('deadline'),
        'estimated_hours': frontmatter.get('estimated_hours'),
        'depends_on': frontmatter.get('depends_on', []),
        'tags': frontmatter.get('tags'),
        'body_markdown': body,
    }
```

---

## 三、Daily Note 时间块解析规格

### 3.1 时间块格式

```markdown
# ⏳ 时间块记录 (Time Blocks)

- [ ] 任务描述文本 (start:: 08:10) (end:: 10:00) (task_uuid:: xxx-xxx) (task_name:: [[task_xxx|task 显示名]])
```

### 3.2 精确正则表达式

```python
import re

# Section header pattern
TIME_BLOCK_SECTION = re.compile(
    r'^#\s*⏳\s*时间块记录\s*\(Time Blocks\)',
    re.MULTILINE
)

# Individual time block pattern
# Groups: (1)checkbox_state (2)description (3)start (4)end (5)task_uuid (6)task_name_path (7)task_display_name
TIME_BLOCK_PATTERN = re.compile(
    r'^- \[(?P<done>.)\] '                           # checkbox: [ ] or [x]
    r'(?P<desc>.+?)'                                  # description (non-greedy)
    r' \(start::\s*(?P<start>\d{1,2}:\d{2})\)'       # (start:: HH:MM)
    r' \(end::\s*(?P<end>\d{1,2}:\d{2})\)'           # (end:: HH:MM)
    r'(?:\s*\(task_uuid::\s*(?P<uuid>[^)]+)\))?'      # optional (task_uuid:: xxx)
    r'(?:\s*\(task_name::\s*\[\[(?P<task_path>[^|\]]+)'  # optional (task_name:: [[path
    r'(?:\|(?P<task_display>[^\]]+))?\]\]\))?',        # optional |display_name]])
    re.MULTILINE
)

def parse_daily_note_time_blocks(file_path: str) -> list:
    """Parse time blocks from a daily note file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the time block section
    section_match = TIME_BLOCK_SECTION.search(content)
    if not section_match:
        return []

    # Get content from section start to next # heading or end of file
    section_start = section_match.end()
    next_heading = re.search(r'^# ', content[section_start:], re.MULTILINE)
    section_end = section_start + next_heading.start() if next_heading else len(content)
    section_content = content[section_start:section_end]

    entries = []
    for match in TIME_BLOCK_PATTERN.finditer(section_content):
        entries.append({
            'done': match.group('done') == 'x',
            'description': match.group('desc').strip(),
            'start': match.group('start'),
            'end': match.group('end'),
            'task_uuid': match.group('uuid'),
            'task_path': match.group('task_path'),
            'task_display': match.group('task_display'),
        })

    return entries
```

---

## 四、VaultWriter 精确写入规格

### 4.1 创建新 Task 文件

**模板：**

```python
TASK_TEMPLATE = """---
task_uuid: {uuid}
task_name: {task_name}
project:
  - "[[{project_ref}]]"
created: {created}
status: {status}
priority: {priority}
deadline: {deadline}
estimated_hours: {estimated_hours}
depends_on: {depends_on}
tags: journal/task
---

# {task_name}

## 任务描述
{description}

## 进展记录
- [ ] {created} 在 [[{daily_note_name}]] 创建任务

## 相关链接
- [[wiki_url]]

## 统计进展情况
```dataviewjs
const taskId = dv.current().task_uuid;
let rows = [];
let total_duration = 0;

for (let page of dv.pages('#journal/daily')) {{
    if (!page.file.tasks) continue;
    for (let t of page.file.tasks) {{
        if (
            t.task_uuid === taskId &&
            t.start && t.end &&
            t.section && t.section.subpath && t.section.subpath.startsWith("⏳ 时间块记录")
        ) {{
            let start = new Date("1970-01-01T" + t.start.padStart(5, '0'));
            let end = new Date("1970-01-01T" + t.end.padStart(5, '0'));
            let duration = Math.round((end - start) / (1000 * 60));
            total_duration += duration;
            rows.push([
                "[[" + page.file.name + "]]",
                t.date || "",
                t.start,
                t.end,
                duration + " 分钟"
            ]);
        }}
    }}
}}

dv.table(["日记", "日期", "开始", "结束", "时长"], rows);
dv.paragraph(`**总耗时**: ${{total_duration}} 分钟`);
```
"""
```

### 4.2 追加时间块到 Daily Note

```python
def append_time_block(daily_note_path: str, entry: dict) -> bool:
    """
    Append a time block entry to the daily note's time block section.

    entry = {
        'description': '实现 VaultReader',
        'start': '14:00',
        'end': '16:30',
        'task_uuid': '693d3007-...',
        'task_name': 'task_implement_vault_reader',
        'task_display': 'task implement vault reader',
    }
    """
    with open(daily_note_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Construct the time block line
    line = (
        f"- [ ] {entry['description']} "
        f"(start:: {entry['start']}) "
        f"(end:: {entry['end']}) "
        f"(task_uuid:: {entry['task_uuid']}) "
        f"(task_name:: [[{entry['task_name']}|{entry['task_display']}]])"
    )

    # Find the time block section and insert before next section
    section_pattern = re.compile(
        r'(#\s*⏳\s*时间块记录\s*\(Time Blocks\).*?)'
        r'((?=\n---\n|\n# ))',
        re.DOTALL
    )

    match = section_pattern.search(content)
    if match:
        insert_pos = match.end(1)
        new_content = content[:insert_pos] + '\n' + line + content[insert_pos:]
    else:
        # Section not found, append at the end (shouldn't happen for valid daily notes)
        new_content = content + '\n' + line

    # Atomic write
    temp_path = daily_note_path + '.tmp'
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    os.replace(temp_path, daily_note_path)  # Atomic on same filesystem

    return True
```

### 4.3 更新 Task Frontmatter

```python
def update_task_frontmatter(task_file_path: str, updates: dict) -> bool:
    """
    Update specific fields in a task file's frontmatter without touching the body.

    updates = {'status': 'doing', 'deadline': '2026-04-05'}
    """
    with open(task_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    match = re.match(r'^---\n(.*?)\n---\n?(.*)', content, re.DOTALL)
    if not match:
        return False

    frontmatter = yaml.safe_load(match.group(1))
    body = match.group(2)

    # Apply updates
    for key, value in updates.items():
        frontmatter[key] = value

    # Reconstruct the file
    new_yaml = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False, sort_keys=False)
    new_content = f"---\n{new_yaml}---\n{body}"

    # Atomic write
    temp_path = task_file_path + '.tmp'
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    os.replace(temp_path, task_file_path)

    return True
```

---

## 五、Daily Note 路径推算规则

```python
from datetime import date

def get_daily_note_path(vault_root: str, target_date: date) -> str:
    """
    Calculate the expected file path for a daily note.

    Logic:
    1. Format filename: "March 21, 2026.md"
    2. Try: VAULT/2_AREA/01-Area-Journal/2026/Daily/March 21, 2026.md
    3. If not found, try: VAULT/2_AREA/01-Area-Journal/2026/Daily/March/March 21, 2026.md
    """
    filename = target_date.strftime("%B %-d, %Y") + ".md"
    year = str(target_date.year)
    month_name = target_date.strftime("%B")

    base = os.path.join(vault_root, "2_AREA", "01-Area-Journal", year, "Daily")

    # Path 1: Directly under Daily/
    path1 = os.path.join(base, filename)
    if os.path.exists(path1):
        return path1

    # Path 2: Under Daily/{MonthName}/
    path2 = os.path.join(base, month_name, filename)
    if os.path.exists(path2):
        return path2

    # Not found — return path1 as default for creation
    return path1
```

---

## 六、缓存同步规则

```python
def sync_vault_to_cache():
    """
    Sync Obsidian vault data to SQLite cache.

    Strategy:
    1. Scan all project directories
    2. For each project, check mtime of tasks/ directory
    3. If mtime > last_sync_time, re-parse all tasks in that project
    4. For daily notes, only scan current month + last month
    5. Store last_sync_time in a SyncMeta table
    """
    # SyncMeta model:
    # | key           | value                | updated_at |
    # | last_sync     | 2026-03-21T10:00:00  | ...        |
    # | vault_hash    | md5-of-directory-list | ...        |
```
