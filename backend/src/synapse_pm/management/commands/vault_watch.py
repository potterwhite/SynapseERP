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
Management command: vault_watch

Start the Obsidian vault filesystem watcher (Phase 5.5 auto-sync).

The watcher monitors the configured vault root directory with watchdog.
When .md files change, it debounces the events and then runs an incremental
import_from_vault() automatically — no manual button click required.

Usage:
    python manage.py vault_watch
    python manage.py vault_watch --debounce 3
    python manage.py vault_watch --once          # sync once then exit

Intended to run as a long-lived background process alongside the Django
development server, or as a separate Systemd unit in production.

Tip:
    ./synapse vault:watch        # convenience alias in the synapse orchestrator
"""

from __future__ import annotations

import logging
import time

from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger("synapse_pm")


class Command(BaseCommand):
    help = (
        "Watch the Obsidian vault for changes and automatically sync to DB. "
        "Press Ctrl-C to stop."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--debounce",
            type=float,
            default=5.0,
            metavar="SECONDS",
            help=(
                "Seconds of inactivity after the last file event before a sync "
                "is triggered. Default: 5. Increase for slow machines."
            ),
        )
        parser.add_argument(
            "--once",
            action="store_true",
            default=False,
            help="Run a single import_from_vault() immediately and exit (no watching).",
        )

    def handle(self, *args, **options):
        debounce: float = options["debounce"]
        once: bool = options["once"]

        from synapse_pm.vault.sync_service import ObsidianSyncService, get_vault_path
        from synapse_pm.vault.vault_watcher import VaultWatcher

        # ----------------------------------------------------------
        # --once: run one import and exit
        # ----------------------------------------------------------
        if once:
            svc = ObsidianSyncService()
            if not svc.enabled:
                raise CommandError(
                    "Vault sync is disabled — no valid vault path configured."
                )
            self.stdout.write(f"Vault path: {svc.vault_root}")
            self.stdout.write("Mode: --once, running single import …")
            result = svc.import_from_vault()
            self._print_result(result)
            return

        # ----------------------------------------------------------
        # Continuous watch mode
        # ----------------------------------------------------------
        vault_path = get_vault_path()
        if not vault_path:
            raise CommandError(
                "Vault sync is disabled — no valid vault path configured.\n"
                "Set OBSIDIAN_VAULT_PATH in backend/.env, or add a SyncMeta "
                "record with key='vault_path' via the Admin UI."
            )

        self.stdout.write(self.style.SUCCESS(
            f"🔍  Watching vault: {vault_path}"
        ))
        self.stdout.write(
            f"    Debounce : {debounce}s  |  Press Ctrl-C to stop\n"
        )

        watcher = VaultWatcher(vault_root=vault_path, debounce_seconds=debounce)

        try:
            watcher.start()
        except RuntimeError as exc:
            raise CommandError(str(exc)) from exc

        # Keep the main thread alive; log a heartbeat every 60 s so operators
        # know the watcher is still running in tmux / systemd journal.
        try:
            heartbeat_interval = 60
            last_heartbeat = time.monotonic()
            while watcher.is_alive():
                time.sleep(1)
                if time.monotonic() - last_heartbeat >= heartbeat_interval:
                    self.stdout.write(
                        f"[vault_watch] still running — syncs so far: {watcher.sync_count}"
                    )
                    last_heartbeat = time.monotonic()
        except KeyboardInterrupt:
            self.stdout.write("\nStopping…")
        finally:
            watcher.stop()
            self.stdout.write(
                self.style.SUCCESS(
                    f"VaultWatcher stopped. Total syncs performed: {watcher.sync_count}"
                )
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _print_result(self, result) -> None:
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
