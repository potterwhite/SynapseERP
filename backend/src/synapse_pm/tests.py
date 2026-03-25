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
Unit tests for synapse_pm.

Focus areas:
  - ObsidianSyncService.import_from_vault: no duplicates when vault path changes
  - Task vault_path is updated even when skip (mtime unchanged)
"""

import os
import tempfile
import textwrap
import time
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

from django.test import TestCase

from synapse_pm.models import Project, Task, SyncMeta
from synapse_pm.vault.sync_service import ObsidianSyncService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_vault(base_dir: str) -> str:
    """
    Create a minimal PARA-style vault inside base_dir.

    Structure:
      base_dir/
        1_PROJECT/
          2025.01_Project_Alpha/
            tasks/
              task_alpha_1.md
    """
    vault = os.path.join(base_dir, "vault")
    proj_dir = os.path.join(vault, "1_PROJECT", "2025.01_Project_Alpha")
    tasks_dir = os.path.join(proj_dir, "tasks")
    os.makedirs(tasks_dir)

    task_uuid = str(uuid.uuid4())
    task_content = textwrap.dedent(f"""\
        ---
        task_uuid: {task_uuid}
        task_name: Alpha Task One
        status: todo
        priority: medium
        ---
        # Alpha Task One

        Task body here.
    """)
    task_file = os.path.join(tasks_dir, "task_alpha_1.md")
    with open(task_file, "w", encoding="utf-8") as f:
        f.write(task_content)

    return vault, task_uuid


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class ImportFromVaultNoDuplicateTest(TestCase):
    """
    Regression test for: re-importing after vault path change must NOT create
    duplicate Project records.  The fix uses full_name as the stable identifier.
    """

    def test_no_duplicate_projects_on_path_change(self):
        """
        1. Create vault at path_A, import → 1 project in DB.
        2. Move vault to path_B (simulate by recreating vault at new temp dir).
        3. Import again from path_B → still only 1 project (updated vault_path).
        """
        with tempfile.TemporaryDirectory() as dir_a:
            vault_a, task_uuid = _make_vault(dir_a)

            # First import from vault_a
            svc_a = ObsidianSyncService(vault_root=vault_a)
            result_a = svc_a.import_from_vault()

            self.assertEqual(Project.objects.count(), 1, "Initial import should create 1 project")
            self.assertEqual(result_a.projects_created, 1)
            self.assertEqual(result_a.projects_updated, 0)

            proj_before = Project.objects.first()
            self.assertEqual(proj_before.vault_path, os.path.join(vault_a, "1_PROJECT", "2025.01_Project_Alpha"))

        # dir_a is gone now; simulate vault relocation to a new directory
        with tempfile.TemporaryDirectory() as dir_b:
            vault_b, _same_task_uuid = _make_vault(dir_b)

            # Overwrite task file with same UUID so tasks don't duplicate either
            proj_dir_b = os.path.join(vault_b, "1_PROJECT", "2025.01_Project_Alpha")
            tasks_dir_b = os.path.join(proj_dir_b, "tasks")
            task_content = textwrap.dedent(f"""\
                ---
                task_uuid: {task_uuid}
                task_name: Alpha Task One
                status: todo
                priority: medium
                ---
                # Alpha Task One
            """)
            with open(os.path.join(tasks_dir_b, "task_alpha_1.md"), "w") as f:
                f.write(task_content)

            # Second import from vault_b (different absolute path, same full_name)
            svc_b = ObsidianSyncService(vault_root=vault_b)
            result_b = svc_b.import_from_vault()

            self.assertEqual(
                Project.objects.count(), 1,
                f"After re-import from relocated vault, must still be 1 project. "
                f"Got {Project.objects.count()}. created={result_b.projects_created} updated={result_b.projects_updated}",
            )
            # vault_path should now point to vault_b location
            proj_after = Project.objects.first()
            self.assertIn(dir_b, proj_after.vault_path,
                          "vault_path should be updated to new location")

    def test_task_vault_path_updated_on_skip(self):
        """
        When a task's mtime is older than DB synced_at (skip), vault_path
        should still be updated if the vault was relocated.
        """
        with tempfile.TemporaryDirectory() as dir_a:
            vault_a, task_uuid = _make_vault(dir_a)
            svc_a = ObsidianSyncService(vault_root=vault_a)
            svc_a.import_from_vault()

            task_before = Task.objects.get(uuid=task_uuid)
            old_vault_path = task_before.vault_path
            self.assertIn(dir_a, old_vault_path)

        with tempfile.TemporaryDirectory() as dir_b:
            vault_b, _ = _make_vault(dir_b)
            # Overwrite with same UUID
            task_content = textwrap.dedent(f"""\
                ---
                task_uuid: {task_uuid}
                task_name: Alpha Task One
                status: todo
                priority: medium
                ---
            """)
            tasks_dir_b = os.path.join(vault_b, "1_PROJECT", "2025.01_Project_Alpha", "tasks")
            with open(os.path.join(tasks_dir_b, "task_alpha_1.md"), "w") as f:
                f.write(task_content)

            svc_b = ObsidianSyncService(vault_root=vault_b)
            svc_b.import_from_vault()

            task_after = Task.objects.get(uuid=task_uuid)
            self.assertIn(dir_b, task_after.vault_path,
                          "Task vault_path must be updated after vault relocation even when skipped")

    def test_truly_new_project_is_still_created(self):
        """
        A project with a full_name that doesn't exist in DB must still be created.
        """
        with tempfile.TemporaryDirectory() as tmp:
            vault, _ = _make_vault(tmp)
            # Add a second project
            new_proj_dir = os.path.join(vault, "1_PROJECT", "2025.02_Project_Beta")
            os.makedirs(os.path.join(new_proj_dir, "tasks"))

            svc = ObsidianSyncService(vault_root=vault)
            result = svc.import_from_vault()

            self.assertEqual(Project.objects.count(), 2)
            self.assertEqual(result.projects_created, 2)
