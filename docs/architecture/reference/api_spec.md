# API 接口规格说明书

> **⚠️ PARTIALLY OUTDATED — FOR AI AGENTS**
> The authentication section (1.2) describes Django Session auth which was
> replaced by JWT in Phase 5.7. For current auth endpoints, see `13_codebase_map.md`
> Section 3 (All REST API Endpoints). All PM/attendance/BOM endpoints remain valid.
>
> 日期：2026-03-21
> 状态：实现规格（认证部分已过时）
> 用途：提供给开发者/AI 的精确 API 契约

---

## 一、通用约定

### 1.1 Base URL

```
Development: http://localhost:8000/api/
Production:  https://your-domain.com/api/
```

### 1.2 认证

**Phase 1 (个人模式)：** Django Session Authentication

```
POST /api/auth/login/
Content-Type: application/json

{"username": "admin", "password": "xxx"}

→ 200 OK + Set-Cookie: sessionid=xxx
```

**Phase 6+ (团队模式)：** JWT (预留)

```
POST /api/auth/token/
→ {"access": "eyJ...", "refresh": "eyJ..."}

Authorization: Bearer eyJ...
```

### 1.3 分页

```json
// Request
GET /api/pm/tasks/?page=1&page_size=20

// Response
{
  "count": 150,
  "next": "http://localhost:8000/api/pm/tasks/?page=2",
  "previous": null,
  "results": [...]
}
```

### 1.4 错误格式

```json
// 400 Bad Request
{"detail": "Invalid input.", "errors": {"field_name": ["Error message"]}}

// 401 Unauthorized
{"detail": "Authentication credentials were not provided."}

// 404 Not Found
{"detail": "Not found."}

// 500 Internal Server Error
{"detail": "Internal server error."}
```

---

## 二、Health Check

### `GET /api/health/`

**无需认证**

```json
// Response 200
{
  "status": "ok",
  "version": "0.9.0",
  "pm_backend": "vault",        // "vault" | "database"
  "vault_connected": true,      // 仅 vault 模式
  "vault_path": "/path/to/vault"
}
```

---

## 三、Dashboard API

### `GET /api/dashboard/`

```json
// Response 200
{
  "notification": {
    "id": 1,
    "content_html": "<h1>System Notice</h1><p>...</p>",
    "updated_at": "2026-03-21T08:00:00Z"
  },
  "modules": [
    {
      "name": "pm",
      "display_name": "Project Management",
      "description": "Manage projects and tasks",
      "url": "/pm",
      "icon": "folder-outline"
    },
    {
      "name": "attendance",
      "display_name": "Attendance Analyzer",
      "description": "Analyze employee attendance data",
      "url": "/attendance",
      "icon": "time-outline"
    },
    {
      "name": "bom",
      "display_name": "BOM Analyzer",
      "description": "Aggregate BOM materials",
      "url": "/bom",
      "icon": "document-outline"
    }
  ]
}
```

---

## 四、Project Management API

### 4.1 `GET /api/pm/projects/`

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `status` | string | `active` / `archived` / `all` (default: `active`) |
| `search` | string | 按名称搜索 |
| `ordering` | string | `name` / `-created` / `deadline` |
| `page` | int | 页码 |
| `page_size` | int | 每页条数 (default: 20, max: 100) |

```json
// Response 200
{
  "count": 15,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Synapse",
      "full_name": "2025.19_Project_Synapse",
      "para_type": "project",
      "status": "active",
      "created": "2025-09-01",
      "deadline": null,
      "vault_path": "1_PROJECT/2025.19_Project_Synapse",
      "task_stats": {
        "total": 4,
        "todo": 1,
        "doing": 1,
        "done": 2,
        "cancelled": 0,
        "completion_rate": 0.5
      },
      "total_hours": 45.5,
      "updated_at": "2026-03-21T08:00:00Z"
    }
  ]
}
```

### 4.2 `GET /api/pm/projects/{id}/`

```json
// Response 200
{
  "id": 1,
  "name": "Synapse",
  "full_name": "2025.19_Project_Synapse",
  "para_type": "project",
  "status": "active",
  "created": "2025-09-01",
  "deadline": null,
  "description": "A modular Django framework for data analysis tools",
  "vault_path": "1_PROJECT/2025.19_Project_Synapse",
  "task_stats": { ... },
  "total_hours": 45.5,
  "tasks": [
    {
      "id": 1,
      "uuid": "693d3007-...",
      "name": "task_setup_framework",
      "display_name": "Setup Framework",
      "status": "done",
      "priority": "high",
      "created": "2025-09-01",
      "deadline": "2025-09-15",
      "estimated_hours": 8,
      "actual_hours": 6.5
    }
  ]
}
```

### 4.3 `GET /api/pm/tasks/`

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `project` | int | 按项目 ID 过滤 |
| `status` | string | `todo` / `doing` / `done` / `cancelled` |
| `priority` | string | `low` / `medium` / `high` |
| `search` | string | 按名称搜索 |
| `has_deadline` | bool | 是否有 deadline（甘特图筛选用） |

```json
// Response 200
{
  "count": 50,
  "results": [
    {
      "id": 1,
      "uuid": "693d3007-e356-418f-9863-5d8a3fe38b89",
      "name": "task_打算扩建synapse_自建一个做PM",
      "display_name": "扩建 Synapse — 自建 PM 系统",
      "project": {
        "id": 1,
        "name": "Synapse"
      },
      "status": "todo",
      "priority": "medium",
      "created": "2026-03-21",
      "deadline": "2026-04-15",
      "estimated_hours": 40,
      "actual_hours": 0,
      "depends_on": [],
      "vault_path": "1_PROJECT/2025.19_Project_Synapse/tasks/task_打算扩建synapse_自建一个做PM.md"
    }
  ]
}
```

### 4.4 `GET /api/pm/tasks/{uuid}/`

```json
// Response 200
{
  "id": 1,
  "uuid": "693d3007-...",
  "name": "task_打算扩建synapse_自建一个做PM",
  "display_name": "扩建 Synapse — 自建 PM 系统",
  "project": { "id": 1, "name": "Synapse" },
  "status": "todo",
  "priority": "medium",
  "created": "2026-03-21",
  "deadline": "2026-04-15",
  "estimated_hours": 40,
  "actual_hours": 12.5,
  "depends_on": [],
  "vault_path": "...",
  "description_markdown": "## 任务描述\n\n...",
  "time_entries": [
    {
      "id": 1,
      "date": "2026-03-21",
      "description": "研究架构方案",
      "start_time": "08:10",
      "end_time": "10:00",
      "duration_minutes": 110,
      "daily_note_path": "2_AREA/01-Area-Journal/2026/Daily/March 21, 2026.md"
    }
  ]
}
```

### 4.5 `POST /api/pm/tasks/`

```json
// Request
{
  "name": "task_implement_gantt_chart",
  "display_name": "实现甘特图功能",
  "project_id": 1,
  "status": "todo",
  "priority": "high",
  "deadline": "2026-04-01",
  "estimated_hours": 16,
  "depends_on": ["uuid-of-other-task"]
}

// Response 201
{
  "id": 10,
  "uuid": "auto-generated-uuid",
  "name": "task_implement_gantt_chart",
  ...
  "vault_path": "1_PROJECT/2025.19_Project_Synapse/tasks/task_implement_gantt_chart.md"
}
```

### 4.6 `PATCH /api/pm/tasks/{uuid}/`

```json
// Request (只发送要修改的字段)
{
  "status": "doing",
  "deadline": "2026-04-05"
}

// Response 200
{ ... updated task object ... }
```

### 4.7 `POST /api/pm/time-entries/`

```json
// Request
{
  "task_uuid": "693d3007-...",
  "date": "2026-03-21",
  "description": "实现 VaultReader",
  "start_time": "14:00",
  "end_time": "16:30"
}

// Response 201
{
  "id": 5,
  "task_uuid": "693d3007-...",
  "date": "2026-03-21",
  "description": "实现 VaultReader",
  "start_time": "14:00",
  "end_time": "16:30",
  "duration_minutes": 150,
  "written_to_daily_note": true   // 是否已写入 Obsidian daily note
}
```

### 4.8 `GET /api/pm/gantt/`

**甘特图专用接口——扁平化所有任务，适合甘特图渲染**

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `project` | int | 按项目过滤 |
| `date_from` | date | 时间范围起始 |
| `date_to` | date | 时间范围结束 |

```json
// Response 200
{
  "tasks": [
    {
      "id": "693d3007-...",
      "name": "扩建 Synapse PM",
      "start": "2026-03-21",
      "end": "2026-04-15",
      "progress": 0,
      "dependencies": "",
      "custom_class": "bar-todo",
      "project_name": "Synapse"
    },
    {
      "id": "uuid-2",
      "name": "实现甘特图",
      "start": "2026-03-25",
      "end": "2026-04-01",
      "progress": 30,
      "dependencies": "693d3007-...",
      "custom_class": "bar-doing",
      "project_name": "Synapse"
    }
  ]
}
```

> 注：`custom_class` 字段对应 frappe-gantt 的 CSS class，用于不同状态的颜色。
> `dependencies` 是逗号分隔的 task ID 列表。

### 4.9 `GET /api/pm/stats/`

```json
// Response 200
{
  "total_projects": 15,
  "active_projects": 12,
  "archived_projects": 3,
  "total_tasks": 87,
  "tasks_by_status": {
    "todo": 30,
    "doing": 15,
    "done": 40,
    "cancelled": 2
  },
  "total_hours_logged": 450.5,
  "hours_this_week": 25.0,
  "overdue_tasks": 3
}
```

### 4.10 `POST /api/pm/sync/`

**触发 Vault 同步（仅 vault 模式）**

```json
// Request (无 body)
POST /api/pm/sync/

// Response 200
{
  "status": "completed",
  "projects_synced": 15,
  "tasks_synced": 87,
  "time_entries_synced": 450,
  "duration_ms": 1200
}
```

---

## 五、Attendance Analyzer API

### 5.1 `POST /api/attendance/analyze/`

```
Content-Type: multipart/form-data

excel_file: (binary file)
```

```json
// Response 200
{
  "filename": "考勤数据_202603.xlsx",
  "analysis_id": "session-key-xxx",
  "detailed_report": {
    "headers": ["姓名", "工作日", "缺勤天数", "详情"],
    "rows": [
      ["张三", 22, 0, "全勤"],
      ["李四", 22, 2, "3/5 缺勤\n3/12 缺勤"]
    ]
  },
  "public_report": {
    "headers": ["姓名", "工作日", "考勤状态"],
    "rows": [
      ["张三", 22, "正常"],
      ["李四", 22, "异常"]
    ]
  }
}
```

### 5.2 `GET /api/attendance/download/?report_type=detailed&lang=zh-hans`

```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="report.xlsx"

(binary Excel file)
```

---

## 六、BOM Analyzer API

### 6.1 `POST /api/bom/analyze/`

```
Content-Type: multipart/form-data

bom_files: (multiple binary files)
```

```json
// Response 200
{
  "filenames": ["BOM_A.xlsx", "BOM_B.xlsx"],
  "analysis_id": "session-key-xxx",
  "report": {
    "headers": ["序号", "物料名称", "规格", "总数量", "数量明细", "异常"],
    "rows": [
      {
        "values": [1, "电阻 10K", "0603", 100, "BOM_A: 50\nBOM_B: 50", false],
        "is_suspicious": false
      }
    ]
  }
}
```

### 6.2 `GET /api/bom/download/`

```
(binary Excel file)
```

---

## 七、Auth API (Phase 1 简化版)

### 7.1 `POST /api/auth/login/`

```json
// Request
{"username": "admin", "password": "xxx"}

// Response 200
{
  "user": {
    "id": 1,
    "username": "admin",
    "is_staff": true
  }
}
// + Set-Cookie: sessionid=xxx; csrftoken=xxx
```

### 7.2 `POST /api/auth/logout/`

```json
// Response 200
{"detail": "Successfully logged out."}
```

### 7.3 `GET /api/auth/me/`

```json
// Response 200
{
  "id": 1,
  "username": "admin",
  "is_staff": true
}
```

---

## 八、Settings API

### 8.1 `GET /api/settings/`

```json
// Response 200
{
  "pm_backend": "vault",
  "vault_path": "/home/username/syncthing/ObsidianVault/PARA-Vault",
  "vault_connected": true,
  "language": "zh-hans",
  "available_languages": ["en", "zh-hans"]
}
```

### 8.2 `PATCH /api/settings/`

```json
// Request
{"language": "en"}

// Response 200
{ ... updated settings ... }
```
