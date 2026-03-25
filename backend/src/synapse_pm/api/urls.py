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

from django.urls import path
from . import views

urlpatterns = [
    # Projects
    path("projects/", views.project_list, name="pm-project-list"),
    path("projects/<int:project_id>/", views.project_detail, name="pm-project-detail"),

    # Tasks
    path("tasks/", views.task_list, name="pm-task-list"),
    path("tasks/<str:task_uuid>/", views.task_detail, name="pm-task-detail"),

    # Time entries
    path("time-entries/", views.time_entry_list, name="pm-time-entry-list"),

    # Stats
    path("stats/", views.pm_stats, name="pm-stats"),

    # Gantt
    path("gantt/", views.gantt_tasks, name="pm-gantt"),

    # Vault sync — Phase 5.3
    # GET  /api/pm/sync/          → sync status
    # POST /api/pm/sync/          → trigger import or export
    path("sync/", views.sync_status, name="pm-sync-status"),
    path("sync/trigger/", views.sync_trigger, name="pm-sync-trigger"),
    path("sync/config/", views.sync_config, name="pm-sync-config"),
]
