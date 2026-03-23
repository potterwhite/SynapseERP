from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from django.conf import settings

from ..models import Project, Task, TimeEntry
from .base import PMBackendAdapter


class VaultAdapter(PMBackendAdapter):
    """
    PM backend that reads data from an Obsidian vault.
    Used when SYNAPSE_PM_BACKEND = 'vault'.

    This adapter treats the SQLite database as a read-through cache: it
    delegates to the cached data for listing/reading, and triggers a
    sync against the vault when needed. Write operations go to both the
    vault (via VaultWriter) and the cache.
    """

    def __init__(self) -> None:
        from ..vault.reader import VaultReader
        self._reader = VaultReader(settings.OBSIDIAN_VAULT_PATH)

    # ------------------------------------------------------------------
    # Internal helpers (re-use DatabaseAdapter serialisation)
    # ------------------------------------------------------------------

    @staticmethod
    def _project_to_dict(p: Project) -> dict[str, Any]:
        from .db_adapter import DatabaseAdapter
        return DatabaseAdapter._project_to_dict(p)

    @staticmethod
    def _task_to_dict(t: Task, *, include_time_entries: bool = False) -> dict[str, Any]:
        from .db_adapter import DatabaseAdapter
        return DatabaseAdapter._task_to_dict(t, include_time_entries=include_time_entries)

    @staticmethod
    def _time_entry_to_dict(e: TimeEntry) -> dict[str, Any]:
        from .db_adapter import DatabaseAdapter
        return DatabaseAdapter._time_entry_to_dict(e)

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
        from .db_adapter import DatabaseAdapter
        db = DatabaseAdapter()
        return db.list_tasks(project_id=project_id, status=status, priority=priority)

    def get_task(self, task_uuid: str) -> dict[str, Any] | None:
        from .db_adapter import DatabaseAdapter
        db = DatabaseAdapter()
        return db.get_task(task_uuid)

    def create_task(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a task: writes to the Obsidian vault first, then upserts
        the cache entry.
        """
        from ..vault.writer import VaultWriter
        from .db_adapter import DatabaseAdapter

        writer = VaultWriter(settings.OBSIDIAN_VAULT_PATH)
        task_data = writer.create_task_file(data)

        # Merge vault-assigned fields back (e.g. generated uuid, vault_path)
        data.update(task_data)
        db = DatabaseAdapter()
        return db.create_task(data)

    def update_task(self, task_uuid: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Update a task: writes frontmatter changes to the vault, then
        updates the cache.
        """
        from ..vault.writer import VaultWriter
        from .db_adapter import DatabaseAdapter

        try:
            task = Task.objects.get(uuid=task_uuid)
        except Task.DoesNotExist:
            return None

        if task.vault_path:
            writer = VaultWriter(settings.OBSIDIAN_VAULT_PATH)
            writer.update_task_frontmatter(task.vault_path, data)

        db = DatabaseAdapter()
        return db.update_task(task_uuid, data)

    # ------------------------------------------------------------------
    # Time Entries
    # ------------------------------------------------------------------

    def list_time_entries(self, *, task_uuid: str) -> list[dict[str, Any]]:
        from .db_adapter import DatabaseAdapter
        db = DatabaseAdapter()
        return db.list_time_entries(task_uuid=task_uuid)

    def create_time_entry(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Log a time entry: appends to the Obsidian daily note, then saves
        to the cache.
        """
        from ..vault.writer import VaultWriter
        from .db_adapter import DatabaseAdapter

        writer = VaultWriter(settings.OBSIDIAN_VAULT_PATH)
        target_date = date.fromisoformat(data["date"]) if isinstance(data["date"], str) else data["date"]
        writer.append_time_block(target_date, data)

        db = DatabaseAdapter()
        return db.create_time_entry(data)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> dict[str, Any]:
        from .db_adapter import DatabaseAdapter
        db = DatabaseAdapter()
        return db.get_stats()

    # ------------------------------------------------------------------
    # Gantt
    # ------------------------------------------------------------------

    def list_gantt_tasks(self, *, project_id: int | None = None) -> list[dict[str, Any]]:
        from .db_adapter import DatabaseAdapter
        db = DatabaseAdapter()
        return db.list_gantt_tasks(project_id=project_id)
