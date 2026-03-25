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

Phase 5.2 (2026-03-25): Switched to DB-Primary architecture.
The database is the sole source of truth. Obsidian vault integration
is handled by a separate sync service (see services/).

Usage:
    from synapse_pm.adapters import get_adapter

    adapter = get_adapter()
    projects = adapter.list_projects()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import PMBackendAdapter


def get_adapter() -> "PMBackendAdapter":
    """
    Return the DatabaseAdapter (DB-Primary architecture).

    Since Phase 5.2, the database is always the source of truth.
    Obsidian vault sync is handled separately via the sync service.
    """
    from .db_adapter import DatabaseAdapter
    return DatabaseAdapter()


__all__ = ["get_adapter", "PMBackendAdapter"]
