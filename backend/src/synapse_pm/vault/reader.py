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
VaultReader: reads project and task data from an Obsidian PARA vault.

Directory conventions (from docs/architecture/plan/11_obsidian_parsing_rules.md):

  VAULT_ROOT/
  ├── 1_PROJECT/
  │   └── 2025.19_Project_Synapse/      ← one project per sub-directory
  │       └── tasks/
  │           └── task_xxx.md           ← one task per .md file
  ├── 4_ARCHIVE/
  │   └── Completed_Projects/
  │       └── ...                        ← archived projects, same layout
  └── 2_AREA/
      └── 01-Area-Journal/
          └── 2026/
              └── Daily/
                  ├── March 21, 2026.md  ← daily notes (may be in month sub-dir)
                  └── March/
                      └── March 21, 2026.md
"""

from __future__ import annotations

import os
import re
from datetime import date, datetime, time
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Compiled patterns (from spec doc)
# ---------------------------------------------------------------------------

# Project directory name: "2025.19_Project_Synapse" → name="Synapse"
PROJECT_NAME_RE = re.compile(r"^(\d{4}\.\d+)_(?:Project_)?(.+)$")

# Task file name: any .md file in tasks/ dir (identified by frontmatter, not filename).
# Skip Syncthing conflict copies.
SYNC_CONFLICT_RE = re.compile(r"\.sync-conflict-.*\.md$")

# YAML frontmatter block
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)", re.DOTALL)

# Wikilink extraction: "[[2025.19_Project_Synapse]]" → "2025.19_Project_Synapse"
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")

# Time block section header
TIME_BLOCK_SECTION_RE = re.compile(
    r"^#\s*⏳\s*时间块记录\s*\(Time Blocks\)",
    re.MULTILINE,
)

# Individual time block entry (named groups)
TIME_BLOCK_RE = re.compile(
    r"^- \[(?P<done>.)\] "
    r"(?P<desc>.+?)"
    r" \(start::\s*(?P<start>\d{1,2}:\d{2})\)"
    r" \(end::\s*(?P<end>\d{1,2}:\d{2})\)"
    r"(?:\s*\(task_uuid::\s*(?P<uuid>[^)]+)\))?"
    r"(?:\s*\(task_name::\s*\[\[(?P<task_path>[^|\]]+)"
    r"(?:\|(?P<task_display>[^\]]+))?\]\]\))?",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# VaultReader
# ---------------------------------------------------------------------------

class VaultReader:
    """
    Reads projects, tasks, and time entries from an Obsidian PARA vault.
    All paths returned are absolute strings.
    """

    def __init__(self, vault_root: str) -> None:
        self.vault_root = vault_root
        self.project_dir = os.path.join(vault_root, "1_PROJECT")
        self.archive_dir = os.path.join(vault_root, "4_ARCHIVE", "Completed_Projects")
        self.area_dir = os.path.join(vault_root, "2_AREA")

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def scan_projects(self) -> list[dict[str, Any]]:
        """
        Scan 1_PROJECT/ and 4_ARCHIVE/Completed_Projects/ for project
        directories.  Returns a list of project dicts.
        """
        projects: list[dict[str, Any]] = []

        for base_dir, para_type, default_status in [
            (self.project_dir, "project", "active"),
            (self.archive_dir, "archive", "archived"),
        ]:
            if not os.path.isdir(base_dir):
                continue
            for entry in sorted(os.scandir(base_dir), key=lambda e: e.name):
                if not entry.is_dir():
                    continue
                name, full_name = self._parse_project_name(entry.name)
                projects.append({
                    "name": name,
                    "full_name": full_name,
                    "para_type": para_type,
                    "status": default_status,
                    "vault_path": entry.path,
                    "vault_mtime": entry.stat().st_mtime,
                    "deadline": None,
                    "created": None,
                })

        return projects

    @staticmethod
    def _parse_project_name(dir_name: str) -> tuple[str, str]:
        """
        "2025.19_Project_Synapse" → ("Synapse", "2025.19_Project_Synapse")
        Falls back to (dir_name, dir_name) if pattern does not match.
        """
        m = PROJECT_NAME_RE.match(dir_name)
        if m:
            return m.group(2), dir_name
        return dir_name, dir_name

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    def scan_tasks(self, project_path: str) -> list[dict[str, Any]]:
        """
        Scan the tasks/ sub-directory of a project directory.

        A file is considered a task if and only if its YAML frontmatter
        contains a ``task_uuid`` field.  The filename prefix is irrelevant.
        Syncthing conflict copies (``*.sync-conflict-*.md``) are skipped.

        Returns a list of parsed task dicts.
        """
        tasks_dir = os.path.join(project_path, "tasks")
        if not os.path.isdir(tasks_dir):
            return []

        tasks: list[dict[str, Any]] = []
        for entry in sorted(os.scandir(tasks_dir), key=lambda e: e.name):
            if not entry.is_file():
                continue
            if not entry.name.endswith(".md"):
                continue
            # Skip Syncthing conflict copies
            if SYNC_CONFLICT_RE.search(entry.name):
                continue
            parsed = self.parse_task_file(entry.path)
            if parsed is None:
                continue
            # A valid task MUST have a task_uuid in its frontmatter
            if not parsed.get("uuid"):
                continue
            parsed["vault_path"] = entry.path
            parsed["vault_mtime"] = entry.stat().st_mtime
            tasks.append(parsed)

        return tasks

    def parse_task_file(self, file_path: str) -> dict[str, Any] | None:
        """
        Parse a task .md file and extract frontmatter + body.
        Returns None if the file has no valid frontmatter.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            return None

        m = FRONTMATTER_RE.match(content)
        if not m:
            return None

        try:
            frontmatter: dict = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError:
            return None

        body = m.group(2)

        # Extract project reference from wikilink list
        project_ref: str | None = None
        raw_project = frontmatter.get("project")
        if isinstance(raw_project, list) and raw_project:
            wl = WIKILINK_RE.search(str(raw_project[0]))
            if wl:
                project_ref = wl.group(1)
        elif isinstance(raw_project, str):
            wl = WIKILINK_RE.search(raw_project)
            if wl:
                project_ref = wl.group(1)

        return {
            "uuid": str(frontmatter.get("task_uuid", "")),
            "name": str(frontmatter.get("task_name", os.path.basename(file_path))),
            "project_ref": project_ref,
            "created": self._parse_date(frontmatter.get("created")),
            "status": str(frontmatter.get("status", "todo")),
            "priority": str(frontmatter.get("priority", "medium")),
            "deadline": self._parse_date(frontmatter.get("deadline")),
            "estimated_hours": frontmatter.get("estimated_hours"),
            "depends_on": frontmatter.get("depends_on") or [],
            "tags": frontmatter.get("tags"),
            "body_markdown": body,
        }

    # ------------------------------------------------------------------
    # Daily notes / Time entries
    # ------------------------------------------------------------------

    def get_daily_note_path(self, target_date: date) -> str:
        """
        Calculate the expected file path for a daily note.

        Search order (per spec):
          1. VAULT/2_AREA/01-Area-Journal/{year}/Daily/{filename}
          2. VAULT/2_AREA/01-Area-Journal/{year}/Daily/{MonthName}/{filename}

        Returns path1 as default (for creation) when neither exists.
        """
        # Linux strftime %-d removes leading zero; %d keeps it
        filename = target_date.strftime("%B %-d, %Y") + ".md"
        year = str(target_date.year)
        month_name = target_date.strftime("%B")

        base = os.path.join(self.area_dir, "01-Area-Journal", year, "Daily")

        path1 = os.path.join(base, filename)
        if os.path.exists(path1):
            return path1

        path2 = os.path.join(base, month_name, filename)
        if os.path.exists(path2):
            return path2

        return path1  # default for creation

    def parse_daily_note_time_blocks(self, file_path: str) -> list[dict[str, Any]]:
        """
        Parse all time block entries from a daily note file.

        Returns a list of dicts with keys:
          done, description, start, end, task_uuid, task_path, task_display
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            return []

        section_match = TIME_BLOCK_SECTION_RE.search(content)
        if not section_match:
            return []

        # Isolate the section content (up to the next top-level heading or EOF)
        section_start = section_match.end()
        next_heading = re.search(r"^# ", content[section_start:], re.MULTILINE)
        section_end = (
            section_start + next_heading.start() if next_heading else len(content)
        )
        section_content = content[section_start:section_end]

        entries: list[dict[str, Any]] = []
        for m in TIME_BLOCK_RE.finditer(section_content):
            start_t = self._parse_time(m.group("start"))
            end_t = self._parse_time(m.group("end"))
            duration = self._calc_duration(start_t, end_t)
            entries.append(
                {
                    "done": m.group("done") == "x",
                    "description": m.group("desc").strip(),
                    "start": m.group("start"),
                    "end": m.group("end"),
                    "start_time": start_t,
                    "end_time": end_t,
                    "duration_minutes": duration,
                    "task_uuid": (m.group("uuid") or "").strip() or None,
                    "task_path": (m.group("task_path") or "").strip() or None,
                    "task_display": (m.group("task_display") or "").strip() or None,
                }
            )

        return entries

    def aggregate_time_entries(self, task_uuid: str, months: int = 2) -> list[dict[str, Any]]:
        """
        Scan daily notes for the last `months` months and collect all
        time entries that reference the given task UUID.
        """
        today = date.today()
        entries: list[dict[str, Any]] = []

        for offset in range(months):
            # Walk backwards month by month
            year = today.year
            month = today.month - offset
            while month <= 0:
                month += 12
                year -= 1

            # Determine number of days in that month
            import calendar
            _, days_in_month = calendar.monthrange(year, month)

            for day in range(1, days_in_month + 1):
                d = date(year, month, day)
                if d > today:
                    continue
                path = self.get_daily_note_path(d)
                if not os.path.exists(path):
                    continue
                for entry in self.parse_daily_note_time_blocks(path):
                    if entry.get("task_uuid") == task_uuid:
                        entry["date"] = d
                        entry["source_note_path"] = path
                        entries.append(entry)

        return entries

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_date(value: Any) -> date | None:
        if value is None:
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        try:
            return date.fromisoformat(str(value))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_time(value: str) -> time | None:
        try:
            parts = value.split(":")
            return time(int(parts[0]), int(parts[1]))
        except (ValueError, IndexError, AttributeError):
            return None

    @staticmethod
    def _calc_duration(start: time | None, end: time | None) -> int:
        """Return duration in minutes; 0 if either value is missing."""
        if start is None or end is None:
            return 0
        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute
        diff = end_minutes - start_minutes
        return max(0, diff)
