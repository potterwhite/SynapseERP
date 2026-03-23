"""
PM Backend Adapter factory.

Usage:
    from synapse_pm.adapters import get_adapter

    adapter = get_adapter()
    projects = adapter.list_projects()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    from .base import PMBackendAdapter


def get_adapter() -> "PMBackendAdapter":
    """
    Return the appropriate PMBackendAdapter based on SYNAPSE_PM_BACKEND.

    'database' → DatabaseAdapter (default, uses Django ORM)
    'vault'    → VaultAdapter (reads/writes Obsidian markdown files)
    """
    backend = getattr(settings, "SYNAPSE_PM_BACKEND", "database")

    if backend == "vault":
        from .vault_adapter import VaultAdapter
        return VaultAdapter()

    # Default: database
    from .db_adapter import DatabaseAdapter
    return DatabaseAdapter()


__all__ = ["get_adapter", "PMBackendAdapter"]
