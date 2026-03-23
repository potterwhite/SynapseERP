from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from ..models import Project, Task, TimeEntry
from .base import PMBackendAdapter


class DatabaseAdapter(PMBackendAdapter):
    """
    PM backend that reads and writes data via Django ORM.
    Used when SYNAPSE_PM_BACKEND = 'database' (the default).
    """

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _project_to_dict(p: Project) -> dict[str, Any]:
        task_qs = p.tasks.all()
        total = task_qs.count()
        done = task_qs.filter(status=Task.Status.DONE).count()
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
            "task_count": total,
            "done_count": done,
            "completion_rate": round(done / total * 100) if total else 0,
        }

    @staticmethod
    def _task_to_dict(t: Task, *, include_time_entries: bool = False) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": t.pk,
            "uuid": str(t.uuid),
            "name": t.name,
            "project_id": t.project_id,
            "project_name": t.project.name,
            "status": t.status,
            "priority": t.priority,
            "created": t.created.isoformat() if t.created else None,
            "deadline": t.deadline.isoformat() if t.deadline else None,
            "estimated_hours": t.estimated_hours,
            "depends_on": [str(dep.uuid) for dep in t.depends_on.all()],
            "vault_path": t.vault_path,
            "synced_at": t.synced_at.isoformat() if t.synced_at else None,
        }
        if include_time_entries:
            d["time_entries"] = [
                DatabaseAdapter._time_entry_to_dict(e)
                for e in t.time_entries.all()
            ]
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
        qs = Project.objects.prefetch_related("tasks")
        if status:
            qs = qs.filter(status=status)
        return [self._project_to_dict(p) for p in qs]

    def get_project(self, project_id: int) -> dict[str, Any] | None:
        try:
            p = Project.objects.prefetch_related("tasks").get(pk=project_id)
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
        t = Task.objects.create(**data)
        if depends_on_uuids:
            dep_tasks = Task.objects.filter(uuid__in=depends_on_uuids)
            t.depends_on.set(dep_tasks)
        return self._task_to_dict(t)

    def update_task(self, task_uuid: str, data: dict[str, Any]) -> dict[str, Any] | None:
        try:
            t = Task.objects.select_related("project").prefetch_related("depends_on").get(uuid=task_uuid)
        except Task.DoesNotExist:
            return None

        depends_on_uuids: list[str] | None = data.pop("depends_on", None)
        for field, value in data.items():
            setattr(t, field, value)
        t.save()

        if depends_on_uuids is not None:
            dep_tasks = Task.objects.filter(uuid__in=depends_on_uuids)
            t.depends_on.set(dep_tasks)

        return self._task_to_dict(t)

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
