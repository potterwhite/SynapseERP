# Copyright (c) 2026 PotterWhite
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
VaultWriter: writes project and task data back to an Obsidian PARA vault.

Write operations follow the exact format defined in:
  docs/architecture/plan/11_obsidian_parsing_rules.md §四

All writes use atomic temp-file-then-rename to avoid partial writes.
"""

from __future__ import annotations

import os
import re
import uuid as _uuid
from datetime import date, datetime
from typing import Any

import yaml


# Dataviewjs block template embedded in new task files
_DATAVIEWJS_BLOCK = """\
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
```"""


class VaultWriter:
    """
    Writes tasks and time entries to an Obsidian PARA vault.
    """

    def __init__(self, vault_root: str) -> None:
        self.vault_root = vault_root
        self.project_dir = os.path.join(vault_root, "1_PROJECT")
        self.area_dir = os.path.join(vault_root, "2_AREA")

    # ------------------------------------------------------------------
    # Task file creation
    # ------------------------------------------------------------------

    def create_task_file(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new task .md file in the appropriate project tasks/ directory.

        Required keys in data:
          name, project_ref (full_name of the project directory)

        Optional keys:
          uuid, status, priority, created, deadline, estimated_hours,
          depends_on (list of UUID strings), description

        Returns a dict with the vault-assigned fields:
          uuid, vault_path, task_name (file stem)
        """
        task_uuid = str(data.get("uuid") or _uuid.uuid4())
        task_display_name: str = data["name"]
        # Sanitize for filename: replace spaces and special chars with _
        safe_name = re.sub(r"[^\w\-]", "_", task_display_name)
        task_file_stem = f"task_{safe_name}"

        project_ref: str = data.get("project_ref", "")
        tasks_dir = self._find_tasks_dir(project_ref)
        os.makedirs(tasks_dir, exist_ok=True)

        task_file_path = os.path.join(tasks_dir, f"{task_file_stem}.md")

        created_str = self._date_str(data.get("created") or date.today())
        deadline_str = self._date_str(data.get("deadline")) or ""
        estimated_hours = data.get("estimated_hours", "")
        depends_on: list[str] = data.get("depends_on") or []
        description: str = data.get("description", "")
        status: str = data.get("status", "todo")
        priority: str = data.get("priority", "medium")

        # Build the daily note name reference for the "创建任务" log entry
        today_daily = date.today().strftime("%B %-d, %Y")

        frontmatter_obj = {
            "task_uuid": task_uuid,
            "task_name": task_file_stem,
            "project": [f"[[{project_ref}]]"],
            "created": created_str,
            "status": status,
            "priority": priority,
            "tags": "journal/task",
        }
        if deadline_str:
            frontmatter_obj["deadline"] = deadline_str
        if estimated_hours:
            frontmatter_obj["estimated_hours"] = estimated_hours
        if depends_on:
            frontmatter_obj["depends_on"] = depends_on

        fm_yaml = yaml.dump(
            frontmatter_obj,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )

        content = (
            f"---\n{fm_yaml}---\n\n"
            f"# {task_file_stem}\n\n"
            f"## 任务描述\n{description}\n\n"
            f"## 进展记录\n- [ ] {created_str} 在 [[{today_daily}]] 创建任务\n\n"
            f"## 相关链接\n- [[wiki_url]]\n\n"
            f"## 统计进展情况\n{_DATAVIEWJS_BLOCK}\n"
        )

        self._atomic_write(task_file_path, content)

        return {
            "uuid": task_uuid,
            "vault_path": task_file_path,
            "task_name": task_file_stem,
        }

    # ------------------------------------------------------------------
    # Task frontmatter update
    # ------------------------------------------------------------------

    def update_task_frontmatter(self, task_file_path: str, updates: dict[str, Any]) -> bool:
        """
        Update specific fields in a task file's YAML frontmatter without
        touching the body.

        updates = {'status': 'doing', 'deadline': '2026-04-05'}
        Returns True on success, False if the file cannot be parsed.
        """
        try:
            with open(task_file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            return False

        m = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
        if not m:
            return False

        try:
            frontmatter: dict = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError:
            return False

        body = m.group(2)

        # Apply updates (only known frontmatter fields)
        for key, value in updates.items():
            if value is None:
                frontmatter.pop(key, None)
            else:
                frontmatter[key] = value

        new_yaml = yaml.dump(
            frontmatter,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
        new_content = f"---\n{new_yaml}---\n{body}"
        self._atomic_write(task_file_path, new_content)
        return True

    # ------------------------------------------------------------------
    # Time block append
    # ------------------------------------------------------------------

    def append_time_block(self, target_date: date, entry: dict[str, Any]) -> bool:
        """
        Append a time block line to the ⏳ 时间块记录 section of a daily note.

        entry must include:
          description, start (HH:MM), end (HH:MM), task_uuid, task_name,
          task_display (optional alias)

        Returns True on success.
        """
        from .reader import VaultReader
        reader = VaultReader(self.vault_root)
        daily_path = reader.get_daily_note_path(target_date)

        task_name: str = entry.get("task_name", "")
        task_display: str = entry.get("task_display", task_name)
        task_uuid: str = entry.get("task_uuid", "")

        line = (
            f"- [ ] {entry['description']} "
            f"(start:: {entry['start']}) "
            f"(end:: {entry['end']}) "
            f"(task_uuid:: {task_uuid}) "
            f"(task_name:: [[{task_name}|{task_display}]])"
        )

        if not os.path.exists(daily_path):
            # Create a minimal daily note with the section header
            content = (
                f"# {target_date.strftime('%B %-d, %Y')}\n\n"
                f"# ⏳ 时间块记录 (Time Blocks)\n\n{line}\n"
            )
            os.makedirs(os.path.dirname(daily_path), exist_ok=True)
            self._atomic_write(daily_path, content)
            return True

        with open(daily_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find the time block section and append before the next section
        section_re = re.compile(
            r"(#\s*⏳\s*时间块记录\s*\(Time Blocks\)[^\n]*\n)",
            re.MULTILINE,
        )
        section_m = section_re.search(content)

        if section_m:
            # Find the end of this section (next heading at same or higher level)
            after_header = section_m.end()
            next_heading_m = re.search(r"^\n*#+ ", content[after_header:], re.MULTILINE)
            if next_heading_m:
                insert_pos = after_header + next_heading_m.start()
                new_content = content[:insert_pos].rstrip("\n") + "\n" + line + "\n" + content[insert_pos:]
            else:
                new_content = content.rstrip("\n") + "\n" + line + "\n"
        else:
            # Section missing — append at EOF
            new_content = content.rstrip("\n") + "\n\n# ⏳ 时间块记录 (Time Blocks)\n\n" + line + "\n"

        self._atomic_write(daily_path, new_content)
        return True

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _find_tasks_dir(self, project_ref: str) -> str:
        """
        Locate the tasks/ directory for the named project.
        Falls back to creating a new directory under 1_PROJECT/ if not found.
        """
        for base in [self.project_dir, os.path.join(self.vault_root, "4_ARCHIVE", "Completed_Projects")]:
            if not os.path.isdir(base):
                continue
            for entry in os.scandir(base):
                if entry.is_dir() and entry.name == project_ref:
                    return os.path.join(entry.path, "tasks")

        # Fallback: create under 1_PROJECT/
        return os.path.join(self.project_dir, project_ref, "tasks")

    @staticmethod
    def _date_str(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, (date, datetime)):
            return value.isoformat()[:10]
        return str(value)

    @staticmethod
    def _atomic_write(path: str, content: str) -> None:
        """Write content atomically using a temp file + rename."""
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)
