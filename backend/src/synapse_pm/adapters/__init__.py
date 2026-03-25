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
