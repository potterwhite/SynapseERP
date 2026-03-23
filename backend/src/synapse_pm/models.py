import uuid
from django.db import models


class Project(models.Model):
    """
    Represents a project. In vault mode, maps to a directory under
    1_PROJECT/ or 4_ARCHIVE/. In database mode, stored only in SQLite/PG.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"
        ON_HOLD = "on_hold", "On Hold"

    class ParaType(models.TextChoices):
        PROJECT = "project", "Project"   # 1_PROJECT/
        ARCHIVE = "archive", "Archive"   # 4_ARCHIVE/

    name = models.CharField(max_length=255)
    full_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Original directory name (e.g. '2025.19_Project_Synapse')",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    para_type = models.CharField(
        max_length=20, choices=ParaType.choices, default=ParaType.PROJECT
    )
    # Absolute path to the project directory inside the vault (vault mode only)
    vault_path = models.CharField(max_length=1024, blank=True)
    deadline = models.DateField(null=True, blank=True)
    created = models.DateField(null=True, blank=True)
    # mtime of the vault directory at last sync (used for incremental sync)
    vault_mtime = models.FloatField(default=0)
    synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Task(models.Model):
    """
    Represents a task. In vault mode, maps to a task_*.md file inside
    a project's tasks/ subdirectory.
    """

    class Status(models.TextChoices):
        TODO = "todo", "To Do"
        DOING = "doing", "Doing"
        DONE = "done", "Done"
        CANCELLED = "cancelled", "Cancelled"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    # UUID comes from the task file's frontmatter; generated here for DB mode
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=255)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="tasks"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.TODO
    )
    priority = models.CharField(
        max_length=20, choices=Priority.choices, default=Priority.MEDIUM
    )
    created = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    estimated_hours = models.FloatField(null=True, blank=True)
    # Self-referential M2M for task dependencies
    depends_on = models.ManyToManyField(
        "self", symmetrical=False, blank=True, related_name="blocks"
    )
    # Absolute path to the task .md file (vault mode only)
    vault_path = models.CharField(max_length=1024, blank=True)
    vault_mtime = models.FloatField(default=0)
    synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created", "name"]

    def __str__(self) -> str:
        return self.name


class TimeEntry(models.Model):
    """
    A single time block logged against a task.
    In vault mode, parsed from daily note time blocks:
      - [ ] desc (start:: HH:MM) (end:: HH:MM) (task_uuid:: ...) (task_name:: [[...]])
    """

    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="time_entries"
    )
    date = models.DateField()
    description = models.TextField(blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    # Duration stored in minutes for easy aggregation
    duration_minutes = models.PositiveIntegerField(default=0)
    # Path to the daily note this entry was parsed from (vault mode only)
    source_note_path = models.CharField(max_length=1024, blank=True)

    class Meta:
        ordering = ["date", "start_time"]

    def __str__(self) -> str:
        return f"{self.task.name} — {self.date} ({self.duration_minutes} min)"
