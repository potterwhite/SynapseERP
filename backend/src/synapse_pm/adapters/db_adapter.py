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

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from ..models import Project, Task, TimeEntry
from .base import PMBackendAdapter


class DatabaseAdapter(PMBackendAdapter):
    """
    PM backend that reads and writes data via Django ORM.

    Since Phase 5.2 (DB-Primary architecture), this is the sole backend.
    The database is the single source of truth for all PM data.
    """

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _project_to_dict(p: Project) -> dict[str, Any]:
        task_qs = p.tasks.all()
        total = task_qs.count()
        done = task_qs.filter(status=Task.Status.DONE).count()
        doing = task_qs.filter(status=Task.Status.DOING).count()
        todo = task_qs.filter(status=Task.Status.TODO).count()
        cancelled = task_qs.filter(status=Task.Status.CANCELLED).count()

        # Aggregate total hours across all tasks for this project.
        # Uses the prefetched time_entries queryset when available.
        total_minutes = sum(
            e.duration_minutes
            for task in task_qs
            for e in task.time_entries.all()
        )

        return {
            "id": p.pk,
            "name": p.name,
            "full_name": p.full_name,
            "status": p.status,
            "para_type": p.para_type,
            "deadline": p.deadline.isoformat() if p.deadline else None,
            "created": p.created.isoformat() if p.created else None,
            "vault_path": p.vault_path,
            "synced_at": p.synced_at.isoformat() if p.synced_at else None,
            # Nested task_stats object — matches frontend types/pm.ts TaskStats shape
            "task_stats": {
                "total": total,
                "todo": todo,
                "doing": doing,
                "done": done,
                "cancelled": cancelled,
                "completion_rate": round(done / total, 2) if total else 0.0,
            },
            "total_hours": round(total_minutes / 60, 1),
        }

    @staticmethod
    def _task_to_dict(t: Task, *, include_time_entries: bool = False) -> dict[str, Any]:
        time_entries_qs = list(t.time_entries.all())
        actual_minutes = sum(e.duration_minutes for e in time_entries_qs)
        d: dict[str, Any] = {
            "id": t.pk,
            "uuid": str(t.uuid),
            "name": t.name,
            # Nested project summary — matches frontend types/pm.ts Task.project shape
            "project": {"id": t.project_id, "name": t.project.name},
            "status": t.status,
            "priority": t.priority,
            "created": t.created.isoformat() if t.created else None,
            "deadline": t.deadline.isoformat() if t.deadline else None,
            "estimated_hours": t.estimated_hours,
            "actual_hours": round(actual_minutes / 60, 1),
            "depends_on": [str(dep.uuid) for dep in t.depends_on.all()],
            "vault_path": t.vault_path,
            "synced_at": t.synced_at.isoformat() if t.synced_at else None,
        }
        if include_time_entries:
            d["time_entries"] = [
                DatabaseAdapter._time_entry_to_dict(e)
                for e in time_entries_qs
            ]
        else:
            d["time_entries"] = []
        return d

    @staticmethod
    def _time_entry_to_dict(e: TimeEntry) -> dict[str, Any]:
        return {
            "id": e.pk,
            "task_uuid": str(e.task.uuid),
            "date": e.date.isoformat(),
            "description": e.description,
            "start_time": e.start_time.isoformat() if e.start_time else None,
            "end_time": e.end_time.isoformat() if e.end_time else None,
            "duration_minutes": e.duration_minutes,
            "source_note_path": e.source_note_path,
        }

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def list_projects(self, *, status: str | None = None) -> list[dict[str, Any]]:
        qs = Project.objects.prefetch_related("tasks", "tasks__time_entries")
        if status:
            qs = qs.filter(status=status)
        return [self._project_to_dict(p) for p in qs]

    def get_project(self, project_id: int) -> dict[str, Any] | None:
        try:
            p = Project.objects.prefetch_related("tasks", "tasks__time_entries").get(pk=project_id)
        except Project.DoesNotExist:
            return None
        return self._project_to_dict(p)

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    def list_tasks(
        self,
        *,
        project_id: int | None = None,
        status: str | None = None,
        priority: str | None = None,
    ) -> list[dict[str, Any]]:
        qs = Task.objects.select_related("project").prefetch_related("depends_on")
        if project_id is not None:
            qs = qs.filter(project_id=project_id)
        if status:
            qs = qs.filter(status=status)
        if priority:
            qs = qs.filter(priority=priority)
        return [self._task_to_dict(t) for t in qs]

    def get_task(self, task_uuid: str) -> dict[str, Any] | None:
        try:
            t = (
                Task.objects
                .select_related("project")
                .prefetch_related("depends_on", "time_entries")
                .get(uuid=task_uuid)
            )
        except Task.DoesNotExist:
            return None
        return self._task_to_dict(t, include_time_entries=True)

    def create_task(self, data: dict[str, Any]) -> dict[str, Any]:
        depends_on_uuids: list[str] = data.pop("depends_on", [])

        # Only pass fields that exist on the Task model to avoid unexpected
        # keyword argument errors when vault-side keys are present.
        _TASK_FIELDS = {
            "name", "project_id", "status", "priority", "created",
            "deadline", "estimated_hours", "vault_path", "vault_mtime",
            "synced_at", "uuid",
        }
        # Handle project FK: accept either project_id (int) or project_ref (ignored here)
        if "project_id" not in data and "project" in data:
            data["project_id"] = data.pop("project")

        create_kwargs = {k: v for k, v in data.items() if k in _TASK_FIELDS}
        t = Task.objects.create(**create_kwargs)
        if depends_on_uuids:
            dep_tasks = Task.objects.filter(uuid__in=depends_on_uuids)
            t.depends_on.set(dep_tasks)
        return self._task_to_dict(t)

    def update_task(self, task_uuid: str, data: dict[str, Any]) -> dict[str, Any] | None:
        try:
            t = (
                Task.objects
                .select_related("project")
                .prefetch_related("depends_on", "time_entries")
                .get(uuid=task_uuid)
            )
        except Task.DoesNotExist:
            return None

        depends_on_uuids: list[str] | None = data.pop("depends_on", None)

        # Only update fields that belong to the Task model.
        _TASK_FIELDS = {
            "name", "status", "priority", "created",
            "deadline", "estimated_hours", "vault_path", "vault_mtime", "synced_at",
        }
        for field, value in data.items():
            if field in _TASK_FIELDS:
                setattr(t, field, value)
        t.save()

        if depends_on_uuids is not None:
            dep_tasks = Task.objects.filter(uuid__in=depends_on_uuids)
            t.depends_on.set(dep_tasks)

        return self._task_to_dict(t, include_time_entries=True)

    # ------------------------------------------------------------------
    # Time Entries
    # ------------------------------------------------------------------

    def list_time_entries(self, *, task_uuid: str) -> list[dict[str, Any]]:
        qs = TimeEntry.objects.select_related("task").filter(task__uuid=task_uuid)
        return [self._time_entry_to_dict(e) for e in qs]

    def create_time_entry(self, data: dict[str, Any]) -> dict[str, Any]:
        task_uuid = data.pop("task_uuid")
        task = Task.objects.get(uuid=task_uuid)
        e = TimeEntry.objects.create(task=task, **data)
        return self._time_entry_to_dict(e)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> dict[str, Any]:
        total_projects = Project.objects.count()
        active_projects = Project.objects.filter(status=Project.Status.ACTIVE).count()
        all_tasks = Task.objects.all()
        total_tasks = all_tasks.count()
        done_tasks = all_tasks.filter(status=Task.Status.DONE).count()
        doing_tasks = all_tasks.filter(status=Task.Status.DOING).count()
        todo_tasks = all_tasks.filter(status=Task.Status.TODO).count()

        total_minutes = sum(
            e.duration_minutes for e in TimeEntry.objects.all()
        )

        return {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "total_tasks": total_tasks,
            "done_tasks": done_tasks,
            "doing_tasks": doing_tasks,
            "todo_tasks": todo_tasks,
            "total_hours_logged": round(total_minutes / 60, 1),
        }

    # ------------------------------------------------------------------
    # Gantt
    # ------------------------------------------------------------------

    def list_gantt_tasks(self, *, project_id: int | None = None) -> list[dict[str, Any]]:
        qs = (
            Task.objects
            .select_related("project")
            .prefetch_related("depends_on")
            .exclude(status=Task.Status.CANCELLED)
        )
        if project_id is not None:
            qs = qs.filter(project_id=project_id)

        today = date.today()
        result = []
        for t in qs:
            start = t.created or today
            # Gantt end: use deadline if set, otherwise estimate from hours, else +7 days
            if t.deadline:
                end = t.deadline
            elif t.estimated_hours:
                end = start + timedelta(days=max(1, int(t.estimated_hours / 8)))
            else:
                end = start + timedelta(days=7)

            # Ensure end >= start
            if end < start:
                end = start + timedelta(days=1)

            dep_uuids = ",".join(str(dep.uuid) for dep in t.depends_on.all())
            result.append({
                "id": str(t.uuid),
                "name": t.name,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "progress": 100 if t.status == Task.Status.DONE else (50 if t.status == Task.Status.DOING else 0),
                "dependencies": dep_uuids,
                "project_id": t.project_id,
                "project_name": t.project.name,
                "status": t.status,
                "priority": t.priority,
            })

        return result
