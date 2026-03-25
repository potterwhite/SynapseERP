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
Management command: sync_vault

Bidirectional sync between Obsidian vault and the database.

Usage:
    python manage.py sync_vault                 # import vault → DB (incremental)
    python manage.py sync_vault --full          # import vault → DB (full re-sync)
    python manage.py sync_vault --export        # export DB → vault
    python manage.py sync_vault --dry-run       # report changes without writing

The vault path is resolved via:
  1. SyncMeta key "vault_path"  (dynamic, set via Admin UI or API)
  2. settings.OBSIDIAN_VAULT_PATH  (static, from .env)

Requires a valid vault path to be configured. Run is a no-op otherwise.
"""

from __future__ import annotations

import logging

from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger("synapse_pm")


class Command(BaseCommand):
    help = "Sync between Obsidian vault and database (bidirectional)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--full",
            action="store_true",
            default=False,
            help="Ignore mtime cache and re-parse every file (import mode only)",
        )
        parser.add_argument(
            "--export",
            action="store_true",
            default=False,
            help="Export DB records back to vault files (DB → vault). Default is import (vault → DB).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Report what would change without writing anything",
        )

    def handle(self, *args, **options):
        full: bool = options["full"]
        export_mode: bool = options["export"]
        dry_run: bool = options["dry_run"]

        from synapse_pm.vault.sync_service import ObsidianSyncService

        svc = ObsidianSyncService()

        if not svc.enabled:
            self.stdout.write(
                self.style.WARNING(
                    "Vault sync is disabled: no valid vault path configured.\n"
                    "Set OBSIDIAN_VAULT_PATH in backend/.env, or add a SyncMeta "
                    "record with key='vault_path' via the Admin UI."
                )
            )
            return

        self.stdout.write(f"Vault path: {svc.vault_root}")

        if dry_run:
            self.stdout.write(self.style.NOTICE("[dry-run] No changes will be written."))

        if export_mode:
            self.stdout.write("Mode: export (DB → vault)")
            result = svc.export_to_vault(dry_run=dry_run)
        else:
            self.stdout.write(f"Mode: import (vault → DB), full={full}")
            result = svc.import_from_vault(full=full, dry_run=dry_run)

        # Print summary
        self.stdout.write(self.style.SUCCESS("\n=== Sync complete ==="))
        self.stdout.write(
            f"  Projects  : {result.projects_created} created, {result.projects_updated} updated"
        )
        self.stdout.write(
            f"  Tasks     : {result.tasks_created} created, {result.tasks_updated} updated"
        )
        self.stdout.write(
            f"  TimeEntries: {result.time_entries_created} created"
        )
        self.stdout.write(f"  Skipped   : {result.skipped}")

        if result.errors:
            self.stdout.write(self.style.WARNING(f"\n  Errors ({len(result.errors)}):"))
            for err in result.errors:
                self.stdout.write(self.style.WARNING(f"    - {err}"))

        if dry_run:
            self.stdout.write(self.style.NOTICE("[dry-run] Database was NOT modified."))
