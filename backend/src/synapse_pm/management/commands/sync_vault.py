"""
Management command: sync_vault

Syncs data from an Obsidian PARA vault into the SQLite cache.

Usage:
    python manage.py sync_vault           # incremental (default)
    python manage.py sync_vault --full    # full re-sync, ignores mtime cache
    python manage.py sync_vault --dry-run # report changes without writing

Only meaningful when SYNAPSE_PM_BACKEND = 'vault'.  In 'database' mode the
command exits cleanly with an informational message.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger("synapse_pm")


class Command(BaseCommand):
    help = "Sync Obsidian vault data into the SQLite cache (vault mode only)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--full",
            action="store_true",
            default=False,
            help="Ignore mtime cache and re-parse every file",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Report what would change without writing to the database",
        )

    def handle(self, *args, **options):
        full: bool = options["full"]
        dry_run: bool = options["dry_run"]

        if getattr(settings, "SYNAPSE_PM_BACKEND", "database") != "vault":
            self.stdout.write(
                self.style.WARNING(
                    "SYNAPSE_PM_BACKEND is not 'vault' — nothing to sync."
                )
            )
            return

        vault_root: str | None = getattr(settings, "OBSIDIAN_VAULT_PATH", None)
        if not vault_root:
            raise CommandError("OBSIDIAN_VAULT_PATH is not configured.")

        from synapse_pm.vault.reader import VaultReader
        from synapse_pm.models import Project, Task, TimeEntry, SyncMeta

        reader = VaultReader(vault_root)
        stats = {"projects_created": 0, "projects_updated": 0,
                 "tasks_created": 0, "tasks_updated": 0,
                 "time_entries_created": 0, "skipped": 0}

        if dry_run:
            self.stdout.write(self.style.NOTICE("[dry-run] No changes will be written."))

        # ------------------------------------------------------------------
        # 1. Scan and upsert projects
        # ------------------------------------------------------------------
        vault_projects = reader.scan_projects()
        self.stdout.write(f"Found {len(vault_projects)} project directories in vault.")

        project_ref_map: dict[str, Project] = {}  # full_name → Project instance

        for vp in vault_projects:
            mtime: float = vp["vault_mtime"]
            try:
                db_proj = Project.objects.get(vault_path=vp["vault_path"])
                project_ref_map[vp["full_name"]] = db_proj

                if not full and db_proj.vault_mtime >= mtime:
                    stats["skipped"] += 1
                    continue

                if not dry_run:
                    db_proj.name = vp["name"]
                    db_proj.full_name = vp["full_name"]
                    db_proj.status = vp["status"]
                    db_proj.para_type = vp["para_type"]
                    db_proj.vault_mtime = mtime
                    db_proj.synced_at = datetime.now(tz=timezone.utc)
                    db_proj.save()

                stats["projects_updated"] += 1
                self.stdout.write(f"  Updated project: {vp['name']}")

            except Project.DoesNotExist:
                if not dry_run:
                    db_proj = Project.objects.create(
                        name=vp["name"],
                        full_name=vp["full_name"],
                        status=vp["status"],
                        para_type=vp["para_type"],
                        vault_path=vp["vault_path"],
                        vault_mtime=mtime,
                        synced_at=datetime.now(tz=timezone.utc),
                    )
                    project_ref_map[vp["full_name"]] = db_proj
                stats["projects_created"] += 1
                self.stdout.write(f"  Created project: {vp['name']}")

        # ------------------------------------------------------------------
        # 2. Scan tasks for each project
        # ------------------------------------------------------------------
        for vp in vault_projects:
            project_path: str = vp["vault_path"]
            db_proj = project_ref_map.get(vp["full_name"])
            if db_proj is None and not dry_run:
                # Project was just created — re-fetch
                try:
                    db_proj = Project.objects.get(vault_path=project_path)
                    project_ref_map[vp["full_name"]] = db_proj
                except Project.DoesNotExist:
                    continue

            vault_tasks = reader.scan_tasks(project_path)

            for vt in vault_tasks:
                if not vt.get("uuid"):
                    self.stdout.write(
                        self.style.WARNING(f"    Skipping task without UUID: {vt.get('name')}")
                    )
                    continue

                mtime: float = vt["vault_mtime"]

                try:
                    db_task = Task.objects.get(uuid=vt["uuid"])

                    if not full and db_task.vault_mtime >= mtime:
                        stats["skipped"] += 1
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
                        db_task.synced_at = datetime.now(tz=timezone.utc)
                        db_task.save()

                    stats["tasks_updated"] += 1

                except Task.DoesNotExist:
                    if not dry_run and db_proj is not None:
                        db_task = Task.objects.create(
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
                            synced_at=datetime.now(tz=timezone.utc),
                        )
                    stats["tasks_created"] += 1

        # ------------------------------------------------------------------
        # 3. Resolve task dependencies (second pass, all tasks now in DB)
        # ------------------------------------------------------------------
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

        # ------------------------------------------------------------------
        # 4. Sync time entries from recent daily notes
        # ------------------------------------------------------------------
        self.stdout.write("Syncing time entries from daily notes (current + last month)...")

        all_db_task_uuids = list(
            Task.objects.filter(vault_path__gt="").values_list("uuid", flat=True)
        )

        for task_uuid in all_db_task_uuids:
            task_uuid_str = str(task_uuid)
            entries = reader.aggregate_time_entries(task_uuid_str, months=2)
            for entry in entries:
                source_path: str = entry.get("source_note_path", "")
                if not dry_run:
                    _, created = TimeEntry.objects.get_or_create(
                        task__uuid=task_uuid_str,
                        date=entry["date"],
                        start_time=entry.get("start_time"),
                        end_time=entry.get("end_time"),
                        defaults={
                            "task": Task.objects.get(uuid=task_uuid_str),
                            "description": entry.get("description", ""),
                            "duration_minutes": entry.get("duration_minutes", 0),
                            "source_note_path": source_path,
                        },
                    )
                    if created:
                        stats["time_entries_created"] += 1
                else:
                    stats["time_entries_created"] += 1

        # ------------------------------------------------------------------
        # 5. Update SyncMeta
        # ------------------------------------------------------------------
        if not dry_run:
            now_iso = datetime.now(tz=timezone.utc).isoformat()
            SyncMeta.objects.update_or_create(
                key="last_sync_at",
                defaults={"value": now_iso},
            )

        # ------------------------------------------------------------------
        # Summary
        # ------------------------------------------------------------------
        self.stdout.write(self.style.SUCCESS("\n=== Sync complete ==="))
        self.stdout.write(
            f"  Projects  : {stats['projects_created']} created, {stats['projects_updated']} updated"
        )
        self.stdout.write(
            f"  Tasks     : {stats['tasks_created']} created, {stats['tasks_updated']} updated"
        )
        self.stdout.write(
            f"  TimeEntries: {stats['time_entries_created']} created"
        )
        self.stdout.write(f"  Skipped   : {stats['skipped']} (mtime unchanged)")
        if dry_run:
            self.stdout.write(self.style.NOTICE("[dry-run] Database was NOT modified."))
