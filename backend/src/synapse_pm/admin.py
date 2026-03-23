from django.contrib import admin
from .models import Project, Task, TimeEntry


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
