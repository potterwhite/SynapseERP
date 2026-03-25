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
VaultWatcher: filesystem event monitor for the Obsidian vault.

Architecture (Phase 5.5 — Vault auto-sync):
  - Uses watchdog to monitor the vault root directory recursively.
  - Debounces rapid bursts of events (e.g. Obsidian saving many files at once).
  - After the debounce window passes, calls ObsidianSyncService.import_from_vault().
  - Runs in its own daemon thread; the management command keeps the main thread
    alive and handles SIGINT / SIGTERM gracefully.
  - Designed for low CPU / memory footprint: inotify on Linux, FSEvents on macOS,
    ReadDirectoryChangesW on Windows — all OS-native, zero polling.

Debounce strategy:
  - A threading.Timer is reset on each file-system event.
  - The timer fires DEBOUNCE_SECONDS after the last event in the burst.
  - Default 5 s is enough to absorb Obsidian's multi-file save bursts.

Usage (from management command)::

    watcher = VaultWatcher(vault_root="/path/to/vault", debounce_seconds=5)
    watcher.start()
    try:
        while watcher.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

logger = logging.getLogger("synapse_pm")

# Watchdog is an optional dependency — import lazily so the rest of
# the app still works when watchdog is not installed.
try:
    from watchdog.events import FileSystemEvent, FileSystemEventHandler
    from watchdog.observers import Observer

    _WATCHDOG_AVAILABLE = True
except ImportError:  # pragma: no cover
    _WATCHDOG_AVAILABLE = False
    FileSystemEventHandler = object  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Event handler with debounce
# ---------------------------------------------------------------------------

class _DebouncedSyncHandler(FileSystemEventHandler):  # type: ignore[misc]
    """
    Watchdog event handler that debounces file-system events and triggers
    an incremental vault→DB import after a quiet period.

    Only .md files and vault directory changes are considered; hidden files
    (starting with '.') and Syncthing conflict copies are ignored.
    """

    def __init__(self, debounce_seconds: float, on_sync: Any) -> None:
        super().__init__()
        self._debounce = debounce_seconds
        self._on_sync = on_sync          # callable() → None
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()
        self.sync_count: int = 0
        self.last_sync_at: float | None = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_relevant(self, path: str) -> bool:
        """Return True if the changed path should trigger a re-sync."""
        import os
        basename = os.path.basename(path)
        # Ignore hidden files (Obsidian workspace files, .DS_Store, etc.)
        if basename.startswith("."):
            return False
        # Ignore Syncthing conflict copies
        if ".sync-conflict-" in basename:
            return False
        # Only care about markdown files and directory events
        if os.path.isdir(path):
            return True
        return path.endswith(".md")

    def _reset_timer(self) -> None:
        """Cancel any pending timer and start a fresh one."""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce, self._fire)
            self._timer.daemon = True
            self._timer.start()

    def _fire(self) -> None:
        """Called after the debounce window expires — runs the sync."""
        logger.info("VaultWatcher: debounce expired, triggering import_from_vault")
        try:
            self._on_sync()
            self.sync_count += 1
            self.last_sync_at = time.time()
        except Exception as exc:
            logger.error("VaultWatcher: sync error: %s", exc, exc_info=True)

    # ------------------------------------------------------------------
    # Watchdog event callbacks
    # ------------------------------------------------------------------

    def on_modified(self, event: "FileSystemEvent") -> None:
        if not event.is_directory and not self._is_relevant(event.src_path):
            return
        logger.debug("VaultWatcher: modified → %s", event.src_path)
        self._reset_timer()

    def on_created(self, event: "FileSystemEvent") -> None:
        if not self._is_relevant(event.src_path):
            return
        logger.debug("VaultWatcher: created → %s", event.src_path)
        self._reset_timer()

    def on_deleted(self, event: "FileSystemEvent") -> None:
        if not self._is_relevant(event.src_path):
            return
        logger.debug("VaultWatcher: deleted → %s", event.src_path)
        self._reset_timer()

    def on_moved(self, event: "FileSystemEvent") -> None:
        if not self._is_relevant(event.src_path) and not self._is_relevant(event.dest_path):
            return
        logger.debug("VaultWatcher: moved %s → %s", event.src_path, event.dest_path)
        self._reset_timer()

    def cancel_pending(self) -> None:
        """Cancel any pending debounce timer (called on shutdown)."""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None


# ---------------------------------------------------------------------------
# Public VaultWatcher
# ---------------------------------------------------------------------------

class VaultWatcher:
    """
    High-level watcher that owns the watchdog Observer thread.

    Lifecycle::

        watcher = VaultWatcher(vault_root=..., debounce_seconds=5)
        watcher.start()        # begins watching
        watcher.stop()         # stops gracefully
        watcher.is_alive()     # True while observer thread is running

    Attributes:
        sync_count    Number of successful syncs performed since start.
        last_sync_at  Unix timestamp of the last sync (float), or None.
    """

    def __init__(
        self,
        vault_root: str | None = None,
        debounce_seconds: float = 5.0,
    ) -> None:
        self._vault_root = vault_root
        self._debounce = debounce_seconds
        self._observer: Any | None = None
        self._handler: _DebouncedSyncHandler | None = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def vault_root(self) -> str | None:
        """Effective vault root (from arg or dynamic config)."""
        if self._vault_root:
            return self._vault_root
        from synapse_pm.vault.sync_service import get_vault_path
        return get_vault_path()

    @property
    def sync_count(self) -> int:
        return self._handler.sync_count if self._handler else 0

    @property
    def last_sync_at(self) -> float | None:
        return self._handler.last_sync_at if self._handler else None

    # ------------------------------------------------------------------
    # Control
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start watching the vault. Raises RuntimeError if watchdog is not installed."""
        if not _WATCHDOG_AVAILABLE:
            raise RuntimeError(
                "watchdog is not installed. Run: pip install 'watchdog>=4.0'"
            )

        vr = self.vault_root
        if not vr:
            raise RuntimeError(
                "No vault path configured. Set OBSIDIAN_VAULT_PATH in .env or "
                "add a vault_path SyncMeta entry via the Admin UI."
            )

        import os
        if not os.path.isdir(vr):
            raise RuntimeError(f"Vault path does not exist or is not a directory: {vr}")

        def _do_sync() -> None:
            """Run inside the debounce timer — must use Django ORM safely."""
            from synapse_pm.vault.sync_service import ObsidianSyncService
            svc = ObsidianSyncService(vault_root=vr)
            result = svc.import_from_vault()
            logger.info(
                "VaultWatcher auto-sync complete: %s", result.summary()
            )

        self._handler = _DebouncedSyncHandler(
            debounce_seconds=self._debounce,
            on_sync=_do_sync,
        )

        self._observer = Observer()
        self._observer.schedule(self._handler, path=vr, recursive=True)
        self._observer.start()
        logger.info(
            "VaultWatcher started: watching '%s' (debounce=%.1fs)",
            vr, self._debounce,
        )

    def stop(self) -> None:
        """Stop the watcher and cancel any pending debounce timer."""
        if self._handler:
            self._handler.cancel_pending()
        if self._observer and self._observer.is_alive():
            self._observer.stop()
            self._observer.join(timeout=5)
            logger.info("VaultWatcher stopped.")

    def is_alive(self) -> bool:
        """Return True if the observer thread is still running."""
        return bool(self._observer and self._observer.is_alive())
