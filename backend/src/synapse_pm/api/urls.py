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

    # Vault sync
    path("sync/", views.sync_vault, name="pm-sync"),
]
