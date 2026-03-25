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

from django.contrib import admin
from .models import Project, Task, TimeEntry, SyncMeta


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "para_type", "deadline", "synced_at")
    list_filter = ("status", "para_type")
    search_fields = ("name", "full_name")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "status", "priority", "deadline", "synced_at")
    list_filter = ("status", "priority", "project")
    search_fields = ("name",)
    raw_id_fields = ("project",)


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ("task", "date", "start_time", "end_time", "duration_minutes")
    list_filter = ("date",)
    raw_id_fields = ("task",)


@admin.register(SyncMeta)
class SyncMetaAdmin(admin.ModelAdmin):
    """
    Admin UI for SyncMeta key-value store.

    Key entries used by ObsidianSyncService:
      vault_path     — absolute path to the Obsidian vault root (overrides .env)
      last_import_at — ISO datetime of the last successful vault→DB import
      last_export_at — ISO datetime of the last successful DB→vault export
    """
    list_display = ("key", "value", "updated_at")
    search_fields = ("key", "value")
    ordering = ("key",)
