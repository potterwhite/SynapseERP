from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class PMBackendAdapter(ABC):
    """
    Abstract base class for PM data backends.

    Two concrete implementations exist:
      - DatabaseAdapter: reads/writes Django ORM (SQLite / PostgreSQL)
      - VaultAdapter:    reads/writes Obsidian markdown files directly

    All public methods share the same signature so callers are completely
    decoupled from the underlying storage mechanism.
    """

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    @abstractmethod
    def list_projects(self, *, status: str | None = None) -> list[dict[str, Any]]:
        """
        Return a list of project dicts.

        Optional filter:
          status: 'active' | 'archived' | 'on_hold'

        Each dict must include at minimum:
          id, name, full_name, status, para_type, deadline, created,
          vault_path, synced_at
        """

    @abstractmethod
    def get_project(self, project_id: int) -> dict[str, Any] | None:
        """Return a single project dict, or None if not found."""

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    @abstractmethod
    def list_tasks(
        self,
        *,
        project_id: int | None = None,
        status: str | None = None,
        priority: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Return a list of task dicts.

        Optional filters:
          project_id: filter by project
          status:     'todo' | 'doing' | 'done' | 'cancelled'
          priority:   'low' | 'medium' | 'high'

        Each dict must include at minimum:
          id, uuid, name, project_id, status, priority, created,
          deadline, estimated_hours, vault_path, synced_at
        """

    @abstractmethod
    def get_task(self, task_uuid: str) -> dict[str, Any] | None:
        """Return a single task dict (with time_entries list), or None."""

    @abstractmethod
    def create_task(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new task and return the resulting task dict.

        Expected keys in data:
          name, project_id, status, priority, created, deadline,
          estimated_hours, depends_on (list of UUIDs)
        """

    @abstractmethod
    def update_task(self, task_uuid: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Update fields on an existing task and return the updated dict.
        Returns None if the task does not exist.
        """

    # ------------------------------------------------------------------
    # Time Entries
    # ------------------------------------------------------------------

    @abstractmethod
    def list_time_entries(self, *, task_uuid: str) -> list[dict[str, Any]]:
        """
        Return all time entries for a given task UUID.

        Each dict must include:
          id, task_uuid, date, description, start_time, end_time,
          duration_minutes, source_note_path
        """

    @abstractmethod
    def create_time_entry(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Log a new time entry and return the resulting dict.

        Expected keys in data:
          task_uuid, date, description, start_time, end_time,
          duration_minutes
        """

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """
        Return aggregate statistics.

        Returned dict must include:
          total_projects, active_projects,
          total_tasks, done_tasks, doing_tasks, todo_tasks,
          total_hours_logged
        """

    # ------------------------------------------------------------------
    # Gantt helper
    # ------------------------------------------------------------------

    @abstractmethod
    def list_gantt_tasks(self, *, project_id: int | None = None) -> list[dict[str, Any]]:
        """
        Return a flat task list suitable for frappe-gantt rendering.

        Each dict must include:
          id (str UUID), name, start (ISO date), end (ISO date),
          progress (0-100), dependencies (comma-separated UUID str)
        """
