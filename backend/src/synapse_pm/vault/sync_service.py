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
ObsidianSyncService: standalone bidirectional sync between Obsidian vault and DB.

Architecture (Phase 5.3 — DB-Primary + Obsidian-Mirror):
  - DB is always the source of truth.
  - Obsidian vault is a personal "offline client" / mirror.
  - This service provides:
      import_from_vault()  — vault → DB  (parse vault files, upsert to DB)
      export_to_vault()    — DB → vault  (write DB records back to vault files)

Conflict strategy: last-modified-wins
  - Compare DB record's synced_at (as Unix timestamp) vs vault file mtime.
  - Whichever is newer wins and overwrites the other side.

Vault path resolution order:
  1. SyncMeta key "vault_path" (dynamic, set via Admin or API)
  2. Django settings.OBSIDIAN_VAULT_PATH (from .env)
  3. None → sync is disabled
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from django.conf import settings

logger = logging.getLogger("synapse_pm")


# ---------------------------------------------------------------------------
# Vault path helpers
# ---------------------------------------------------------------------------

def get_vault_path() -> str | None:
    """
    Resolve the vault path from SyncMeta (dynamic) or settings (static).

    Returns the absolute path string, or None if not configured.
    """
    # Lazy import to avoid circular imports at module load time
    from synapse_pm.models import SyncMeta
    try:
        meta = SyncMeta.objects.get(key="vault_path")
        if meta.value and meta.value.strip():
            return meta.value.strip()
    except SyncMeta.DoesNotExist:
        pass

    return getattr(settings, "OBSIDIAN_VAULT_PATH", None) or None


def is_sync_enabled() -> bool:
    """Return True if a vault path is configured and the directory exists."""
    path = get_vault_path()
    if not path:
        return False
    return os.path.isdir(path)


# ---------------------------------------------------------------------------
# SyncResult
# ---------------------------------------------------------------------------

class SyncResult:
    """
    Holds statistics for a single sync run.
    """

    def __init__(self) -> None:
        self.projects_created: int = 0
        self.projects_updated: int = 0
        self.tasks_created: int = 0
        self.tasks_updated: int = 0
        self.time_entries_created: int = 0
        self.skipped: int = 0
        self.errors: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "projects_created": self.projects_created,
            "projects_updated": self.projects_updated,
            "tasks_created": self.tasks_created,
            "tasks_updated": self.tasks_updated,
            "time_entries_created": self.time_entries_created,
            "skipped": self.skipped,
            "errors": self.errors,
        }

    def summary(self) -> str:
        return (
            f"Projects: {self.projects_created} created, {self.projects_updated} updated | "
            f"Tasks: {self.tasks_created} created, {self.tasks_updated} updated | "
            f"TimeEntries: {self.time_entries_created} created | "
            f"Skipped: {self.skipped}"
        )


# ---------------------------------------------------------------------------
# ObsidianSyncService
# ---------------------------------------------------------------------------

class ObsidianSyncService:
    """
    Standalone bidirectional sync service between Obsidian vault and DB.

    Usage::

        svc = ObsidianSyncService()
        if not svc.enabled:
            print("Vault sync not configured")
        else:
            result = svc.import_from_vault()   # vault → DB
            result = svc.export_to_vault()     # DB → vault
    """

    def __init__(self, vault_root: str | None = None) -> None:
        """
        Args:
            vault_root: Override vault path. If None, resolved from SyncMeta / settings.
        """
        self._vault_root = vault_root

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def vault_root(self) -> str | None:
        """Effective vault root path, or None if not configured."""
        if self._vault_root:
            return self._vault_root
        return get_vault_path()

    @property
    def enabled(self) -> bool:
        """True if vault is configured and the directory exists."""
        vr = self.vault_root
        return bool(vr and os.path.isdir(vr))

    # ------------------------------------------------------------------
    # Import: vault → DB
    # ------------------------------------------------------------------

    def import_from_vault(
        self,
        *,
        full: bool = False,
        dry_run: bool = False,
        name_filter: list[str] | None = None,
    ) -> SyncResult:
        """
        Import projects, tasks, and time entries from the vault into the DB.

        Conflict strategy: last-modified-wins.
          - If vault file mtime > DB synced_at  → vault wins, update DB.
          - If DB synced_at  >= vault file mtime → DB wins, skip vault record.
          - New records (no UUID match in DB)    → always import.

        Args:
            full:        If True, ignore mtime cache and re-parse every file.
            dry_run:     If True, compute changes but do not write to DB.
            name_filter: Optional list of keywords. When provided, only projects
                         whose ``full_name`` contains at least one keyword
                         (case-insensitive) are imported.  Defaults to None
                         (import all projects).

        Returns:
            SyncResult with statistics.
        """
        result = SyncResult()

        if not self.enabled:
            result.errors.append("Vault sync disabled: no valid vault path configured.")
            return result

        vault_root = self.vault_root
        assert vault_root is not None  # guarded by self.enabled

        from synapse_pm.vault.reader import VaultReader
        from synapse_pm.models import Project, Task, TimeEntry, SyncMeta

        reader = VaultReader(vault_root)
        now = datetime.now(tz=timezone.utc)
        project_ref_map: dict[str, Project] = {}

        # --------------------------------------------------------------
        # Step 1: Scan and upsert projects
        # --------------------------------------------------------------
        vault_projects = reader.scan_projects()
        logger.info("import_from_vault: found %d project directories", len(vault_projects))

        # Optional name filter: keep only projects whose full_name contains
        # at least one of the provided keywords (case-insensitive).
        if name_filter:
            lower_keywords = [kw.lower() for kw in name_filter if kw.strip()]
            if lower_keywords:
                vault_projects = [
                    vp for vp in vault_projects
                    if any(kw in vp["full_name"].lower() for kw in lower_keywords)
                ]
                logger.info(
                    "import_from_vault: filtered to %d projects by name_filter=%r",
                    len(vault_projects), name_filter,
                )

        for vp in vault_projects:
            mtime: float = vp["vault_mtime"]
            db_proj: "Project | None" = None

            # --- Lookup strategy (handles vault-path relocations) -----------
            # 1st: match by full_name (stable, path-independent identifier)
            # 2nd: match by vault_path (legacy / initial import)
            # If neither matches → create new record.
            try:
                db_proj = Project.objects.get(full_name=vp["full_name"])
            except Project.DoesNotExist:
                try:
                    db_proj = Project.objects.get(vault_path=vp["vault_path"])
                except Project.DoesNotExist:
                    db_proj = None

            if db_proj is not None:
                project_ref_map[vp["full_name"]] = db_proj

                # If the vault was relocated, always update vault_path even when
                # skipping (so future mtime comparisons use the correct path).
                vault_path_changed = db_proj.vault_path != vp["vault_path"]

                if not full:
                    # Convert DB synced_at to a comparable timestamp
                    db_ts = db_proj.synced_at.timestamp() if db_proj.synced_at else 0.0
                    if db_ts >= mtime:
                        # DB is up-to-date — only patch vault_path if it moved
                        if vault_path_changed and not dry_run:
                            db_proj.vault_path = vp["vault_path"]
                            db_proj.save(update_fields=["vault_path"])
                            logger.debug(
                                "  Updated vault_path for project: %s → %s",
                                vp["name"], vp["vault_path"],
                            )
                        result.skipped += 1
                        continue

                if not dry_run:
                    db_proj.name = vp["name"]
                    db_proj.full_name = vp["full_name"]
                    db_proj.status = vp["status"]
                    db_proj.para_type = vp["para_type"]
                    db_proj.vault_path = vp["vault_path"]
                    db_proj.vault_mtime = mtime
                    db_proj.synced_at = now
                    db_proj.save()

                result.projects_updated += 1
                logger.debug("  Updated project: %s", vp["name"])

            else:
                # No existing record found → create
                if not dry_run:
                    db_proj = Project.objects.create(
                        name=vp["name"],
                        full_name=vp["full_name"],
                        status=vp["status"],
                        para_type=vp["para_type"],
                        vault_path=vp["vault_path"],
                        vault_mtime=mtime,
                        synced_at=now,
                    )
                    project_ref_map[vp["full_name"]] = db_proj
                result.projects_created += 1
                logger.debug("  Created project: %s", vp["name"])

        # --------------------------------------------------------------
        # Step 2: Scan tasks for each project
        # --------------------------------------------------------------
        for vp in vault_projects:
            project_path: str = vp["vault_path"]
            db_proj = project_ref_map.get(vp["full_name"])

            if db_proj is None and not dry_run:
                try:
                    db_proj = Project.objects.get(vault_path=project_path)
                    project_ref_map[vp["full_name"]] = db_proj
                except Project.DoesNotExist:
                    continue

            vault_tasks = reader.scan_tasks(project_path)

            for vt in vault_tasks:
                if not vt.get("uuid"):
                    logger.warning("Skipping task without UUID: %s", vt.get("name"))
                    continue

                mtime = vt["vault_mtime"]

                try:
                    db_task = Task.objects.get(uuid=vt["uuid"])

                    if not full:
                        db_ts = db_task.synced_at.timestamp() if db_task.synced_at else 0.0
                        if db_ts >= mtime:
                            # DB is up-to-date — patch vault_path if vault was relocated
                            if db_task.vault_path != vt["vault_path"] and not dry_run:
                                db_task.vault_path = vt["vault_path"]
                                db_task.save(update_fields=["vault_path"])
                            result.skipped += 1
                            continue

                    if not dry_run:
                        db_task.name = vt["name"]
                        db_task.status = vt["status"]
                        db_task.priority = vt["priority"]
                        db_task.created = vt.get("created")
                        db_task.deadline = vt.get("deadline")
                        db_task.estimated_hours = vt.get("estimated_hours")
                        db_task.vault_path = vt["vault_path"]
                        db_task.vault_mtime = mtime
                        db_task.synced_at = now
                        db_task.save()

                    result.tasks_updated += 1

                except Task.DoesNotExist:
                    if not dry_run and db_proj is not None:
                        Task.objects.create(
                            uuid=vt["uuid"],
                            name=vt["name"],
                            project=db_proj,
                            status=vt["status"],
                            priority=vt["priority"],
                            created=vt.get("created"),
                            deadline=vt.get("deadline"),
                            estimated_hours=vt.get("estimated_hours"),
                            vault_path=vt["vault_path"],
                            vault_mtime=mtime,
                            synced_at=now,
                        )
                    result.tasks_created += 1

        # --------------------------------------------------------------
        # Step 3: Resolve task dependencies (second pass)
        # --------------------------------------------------------------
        if not dry_run:
            for vp in vault_projects:
                for vt in reader.scan_tasks(vp["vault_path"]):
                    depends_on_uuids: list[str] = vt.get("depends_on") or []
                    if not depends_on_uuids or not vt.get("uuid"):
                        continue
                    try:
                        db_task = Task.objects.get(uuid=vt["uuid"])
                        dep_tasks = Task.objects.filter(uuid__in=depends_on_uuids)
                        db_task.depends_on.set(dep_tasks)
                    except Task.DoesNotExist:
                        pass

        # --------------------------------------------------------------
        # Step 4: Sync time entries from recent daily notes
        # --------------------------------------------------------------
        logger.info("import_from_vault: syncing time entries from daily notes...")

        # Only scan tasks that have a vault_path (came from vault originally,
        # or were previously exported to vault)
        task_uuids_with_vault = list(
            Task.objects.filter(vault_path__gt="").values_list("uuid", flat=True)
        )

        for task_uuid_val in task_uuids_with_vault:
            task_uuid_str = str(task_uuid_val)
            try:
                entries = reader.aggregate_time_entries(task_uuid_str, months=2)
            except Exception as exc:
                logger.error("Error aggregating time entries for task %s: %s", task_uuid_str, exc)
                result.errors.append(f"TimeEntry scan failed for {task_uuid_str}: {exc}")
                continue

            for entry in entries:
                if dry_run:
                    result.time_entries_created += 1
                    continue
                try:
                    _, created = TimeEntry.objects.get_or_create(
                        task__uuid=task_uuid_str,
                        date=entry["date"],
                        start_time=entry.get("start_time"),
                        end_time=entry.get("end_time"),
                        defaults={
                            "task": Task.objects.get(uuid=task_uuid_str),
                            "description": entry.get("description", ""),
                            "duration_minutes": entry.get("duration_minutes", 0),
                            "source_note_path": entry.get("source_note_path", ""),
                        },
                    )
                    if created:
                        result.time_entries_created += 1
                except Exception as exc:
                    logger.error("Error creating time entry: %s", exc)
                    result.errors.append(f"TimeEntry create failed: {exc}")

        # --------------------------------------------------------------
        # Step 5: Update SyncMeta
        # --------------------------------------------------------------
        if not dry_run:
            SyncMeta.objects.update_or_create(
                key="last_import_at",
                defaults={"value": now.isoformat()},
            )

        logger.info("import_from_vault complete: %s", result.summary())
        return result

    # ------------------------------------------------------------------
    # Export: DB → vault
    # ------------------------------------------------------------------

    def export_to_vault(
        self,
        *,
        project_ids: list[int] | None = None,
        dry_run: bool = False,
    ) -> SyncResult:
        """
        Export projects and tasks from DB back to vault files.

        Conflict strategy: DB wins (DB-Primary).
          - If a task has a vault_path and the DB record is newer, overwrite the file.
          - If a task has no vault_path, create a new file in the appropriate project dir.
          - Projects without vault directories are skipped (no directory to write to).

        Args:
            project_ids: If provided, only export tasks belonging to these projects.
            dry_run:     If True, compute what would be written but do not write.

        Returns:
            SyncResult with statistics.
        """
        result = SyncResult()

        if not self.enabled:
            result.errors.append("Vault sync disabled: no valid vault path configured.")
            return result

        vault_root = self.vault_root
        assert vault_root is not None

        from synapse_pm.vault.writer import VaultWriter
        from synapse_pm.models import Project, Task, SyncMeta

        writer = VaultWriter(vault_root)
        now = datetime.now(tz=timezone.utc)

        # Build project queryset
        project_qs = Project.objects.prefetch_related("tasks")
        if project_ids:
            project_qs = project_qs.filter(pk__in=project_ids)

        for project in project_qs:
            task_qs = project.tasks.exclude(status=Task.Status.CANCELLED)
            if project_ids is not None:
                task_qs = task_qs.filter(project_id__in=project_ids)

            for task in task_qs:
                vault_path: str = task.vault_path or ""

                if vault_path and os.path.exists(vault_path):
                    # Conflict check: compare DB synced_at vs file mtime
                    file_mtime = os.path.getmtime(vault_path)
                    db_ts = task.synced_at.timestamp() if task.synced_at else 0.0

                    if db_ts >= file_mtime:
                        # DB is newer or equal — update vault file frontmatter
                        if not dry_run:
                            updates = {
                                "task_name": task.name,
                                "status": task.status,
                                "priority": task.priority,
                                "deadline": task.deadline.isoformat() if task.deadline else None,
                                "estimated_hours": task.estimated_hours,
                            }
                            # Remove None values to avoid overwriting with nulls unnecessarily
                            updates = {k: v for k, v in updates.items() if v is not None}
                            writer.update_task_frontmatter(vault_path, updates)
                        result.tasks_updated += 1
                        logger.debug("  Updated vault task: %s", task.name)
                    else:
                        # Vault is newer — skip (import_from_vault should be run first)
                        result.skipped += 1
                        logger.debug("  Skipped (vault newer): %s", task.name)

                else:
                    # No vault file exists yet — create one.
                    # For projects created in DB (no vault_path), derive the target
                    # directory from the project's full_name under 1_PROJECT/.
                    # The writer's _find_tasks_dir will create the dir if absent.
                    target_project_path = project.vault_path
                    if not target_project_path or not os.path.isdir(target_project_path):
                        # Derive path: vault_root/1_PROJECT/<full_name>
                        candidate = os.path.join(vault_root, "1_PROJECT", project.full_name)
                        target_project_path = candidate

                    if not dry_run:
                        try:
                            write_result = writer.create_task_file({
                                "uuid": str(task.uuid),
                                "name": task.name,
                                "project_ref": project.full_name,
                                "status": task.status,
                                "priority": task.priority,
                                "created": task.created,
                                "deadline": task.deadline,
                                "estimated_hours": task.estimated_hours,
                            })
                            # Update task with new vault_path
                            task.vault_path = write_result["vault_path"]
                            task.vault_mtime = os.path.getmtime(write_result["vault_path"])
                            task.synced_at = now
                            task.save(update_fields=["vault_path", "vault_mtime", "synced_at"])
                            # If the project had no vault_path, update it now
                            if not project.vault_path or not os.path.isdir(project.vault_path):
                                project.vault_path = target_project_path
                                project.save(update_fields=["vault_path"])
                        except Exception as exc:
                            logger.error("Failed to create vault file for task %s: %s", task.name, exc)
                            result.errors.append(f"Export failed for '{task.name}': {exc}")
                            continue
                    result.tasks_created += 1
                    logger.debug("  Created vault task: %s", task.name)

        # Update SyncMeta
        if not dry_run:
            SyncMeta.objects.update_or_create(
                key="last_export_at",
                defaults={"value": now.isoformat()},
            )

        logger.info("export_to_vault complete: %s", result.summary())
        return result

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self) -> dict[str, Any]:
        """
        Return current sync status information.

        Returns a dict suitable for the API response.
        """
        from synapse_pm.models import SyncMeta, Project, Task

        vault_path = self.vault_root
        enabled = self.enabled

        last_import_at: str | None = None
        last_export_at: str | None = None

        try:
            last_import_at = SyncMeta.objects.get(key="last_import_at").value
        except SyncMeta.DoesNotExist:
            pass

        try:
            last_export_at = SyncMeta.objects.get(key="last_export_at").value
        except SyncMeta.DoesNotExist:
            pass

        db_project_count = Project.objects.count() if enabled else 0
        db_task_count = Task.objects.count() if enabled else 0

        # Lightweight vault scan: count project dirs and task .md files
        # using os.scandir only (no file parsing, no I/O beyond directory listing).
        vault_project_count: int | None = None
        vault_task_count: int | None = None
        if enabled and vault_path:
            vault_project_count, vault_task_count = self._count_vault_items(vault_path)

        return {
            "enabled": enabled,
            "vault_path": vault_path,
            "last_import_at": last_import_at,
            "last_export_at": last_export_at,
            "db_projects": db_project_count,
            "db_tasks": db_task_count,
            "vault_projects": vault_project_count,
            "vault_tasks": vault_task_count,
        }

    @staticmethod
    def _count_vault_items(vault_root: str) -> tuple[int, int]:
        """
        Count project directories and task .md files in the vault without
        parsing any file content.  Uses os.scandir for minimal I/O.

        Scans:
          - 1_PROJECT/*/          → project dirs
          - 4_ARCHIVE/Completed_Projects/*/  → archived project dirs
          - {project_dir}/tasks/*.md          → task files (by extension only)

        Returns (project_count, task_count).
        """
        project_dirs: list[str] = []

        for base in [
            os.path.join(vault_root, "1_PROJECT"),
            os.path.join(vault_root, "4_ARCHIVE", "Completed_Projects"),
        ]:
            if not os.path.isdir(base):
                continue
            try:
                for entry in os.scandir(base):
                    if entry.is_dir():
                        project_dirs.append(entry.path)
            except OSError:
                pass

        task_count = 0
        for proj_dir in project_dirs:
            tasks_dir = os.path.join(proj_dir, "tasks")
            if not os.path.isdir(tasks_dir):
                continue
            try:
                for entry in os.scandir(tasks_dir):
                    if not (entry.is_file() and entry.name.endswith(".md")):
                        continue
                    # Only count files that actually contain a task_uuid field.
                    # This avoids counting hand-created .md files that the importer
                    # skips (no UUID), which would cause a permanent off-by-one
                    # between "Tasks in Vault" and "Tasks in DB".
                    # We read only the first 512 bytes (frontmatter is always at top).
                    try:
                        with open(entry.path, "r", encoding="utf-8", errors="ignore") as fh:
                            head = fh.read(512)
                        if "task_uuid" in head:
                            task_count += 1
                    except OSError:
                        pass
            except OSError:
                pass

        return len(project_dirs), task_count
