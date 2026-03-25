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

from rest_framework import serializers
from .models import Project, Task, TimeEntry


class TimeEntrySerializer(serializers.ModelSerializer):
    task_uuid = serializers.UUIDField(source="task.uuid", read_only=True)

    class Meta:
        model = TimeEntry
        fields = [
            "id",
            "task_uuid",
            "date",
            "description",
            "start_time",
            "end_time",
            "duration_minutes",
            "source_note_path",
        ]


class TaskSummarySerializer(serializers.ModelSerializer):
    """Lightweight task serializer used inside project detail."""

    uuid = serializers.UUIDField(read_only=True)
    actual_hours = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "uuid",
            "name",
            "status",
            "priority",
            "created",
            "deadline",
            "estimated_hours",
            "actual_hours",
        ]

    def get_actual_hours(self, obj: Task) -> float:
        total = sum(e.duration_minutes for e in obj.time_entries.all())
        return round(total / 60, 1)


class TaskSerializer(serializers.ModelSerializer):
    """Full task serializer (list + detail)."""

    uuid = serializers.UUIDField(read_only=True)
    project = serializers.SerializerMethodField()
    depends_on = serializers.SerializerMethodField()
    actual_hours = serializers.SerializerMethodField()
    time_entries = TimeEntrySerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "uuid",
            "name",
            "project",
            "status",
            "priority",
            "created",
            "deadline",
            "estimated_hours",
            "actual_hours",
            "depends_on",
            "vault_path",
            "synced_at",
            "time_entries",
        ]
        read_only_fields = ["id", "uuid", "vault_path", "synced_at"]

    def get_project(self, obj: Task) -> dict:
        return {"id": obj.project_id, "name": obj.project.name}

    def get_depends_on(self, obj: Task) -> list[str]:
        return [str(dep.uuid) for dep in obj.depends_on.all()]

    def get_actual_hours(self, obj: Task) -> float:
        total = sum(e.duration_minutes for e in obj.time_entries.all())
        return round(total / 60, 1)


class TaskWriteSerializer(serializers.Serializer):
    """Serializer for POST /tasks/ and PATCH /tasks/{uuid}/."""

    name = serializers.CharField(max_length=255, required=False)
    project_id = serializers.IntegerField(required=False)
    status = serializers.ChoiceField(choices=Task.Status.choices, required=False)
    priority = serializers.ChoiceField(choices=Task.Priority.choices, required=False)
    created = serializers.DateField(required=False, allow_null=True)
    deadline = serializers.DateField(required=False, allow_null=True)
    estimated_hours = serializers.FloatField(required=False, allow_null=True)
    depends_on = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )
    description = serializers.CharField(required=False, allow_blank=True)


class ProjectSerializer(serializers.ModelSerializer):
    """Project serializer for list endpoint."""

    task_stats = serializers.SerializerMethodField()
    total_hours = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "full_name",
            "para_type",
            "status",
            "created",
            "deadline",
            "tags",
            "vault_path",
            "task_stats",
            "total_hours",
            "synced_at",
        ]

    def get_task_stats(self, obj: Project) -> dict:
        tasks = obj.tasks.all()
        total = tasks.count()
        done = tasks.filter(status=Task.Status.DONE).count()
        doing = tasks.filter(status=Task.Status.DOING).count()
        todo = tasks.filter(status=Task.Status.TODO).count()
        cancelled = tasks.filter(status=Task.Status.CANCELLED).count()
        return {
            "total": total,
            "todo": todo,
            "doing": doing,
            "done": done,
            "cancelled": cancelled,
            "completion_rate": round(done / total, 2) if total else 0,
        }

    def get_total_hours(self, obj: Project) -> float:
        total_minutes = sum(
            e.duration_minutes
            for task in obj.tasks.prefetch_related("time_entries").all()
            for e in task.time_entries.all()
        )
        return round(total_minutes / 60, 1)


class ProjectDetailSerializer(ProjectSerializer):
    """Project serializer for detail endpoint (includes task list)."""

    tasks = TaskSummarySerializer(many=True, read_only=True)

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ["tasks"]


class ProjectWriteSerializer(serializers.Serializer):
    """Serializer for POST /projects/ and PATCH /projects/{id}/."""

    name = serializers.CharField(max_length=255, required=False)
    full_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=Project.Status.choices, required=False)
    para_type = serializers.ChoiceField(choices=Project.ParaType.choices, required=False)
    deadline = serializers.DateField(required=False, allow_null=True)
    created = serializers.DateField(required=False, allow_null=True)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=64),
        required=False,
        default=list,
    )


class TimeEntryCreateSerializer(serializers.Serializer):
    """Serializer for POST /pm/time-entries/."""

    task_uuid = serializers.UUIDField()
    date = serializers.DateField()
    description = serializers.CharField(allow_blank=True, default="")
    start_time = serializers.TimeField(required=False, allow_null=True)
    end_time = serializers.TimeField(required=False, allow_null=True)
    duration_minutes = serializers.IntegerField(min_value=0, required=False, default=0)

    def validate(self, data: dict) -> dict:
        start = data.get("start_time")
        end = data.get("end_time")
        if start and end:
            s = start.hour * 60 + start.minute
            e = end.hour * 60 + end.minute
            if e <= s:
                raise serializers.ValidationError("end_time must be after start_time.")
            data["duration_minutes"] = e - s
        return data


class GanttTaskSerializer(serializers.Serializer):
    """Read-only serializer for Gantt chart task items."""

    id = serializers.CharField()
    name = serializers.CharField()
    start = serializers.DateField()
    end = serializers.DateField()
    progress = serializers.IntegerField()
    dependencies = serializers.CharField(allow_blank=True)
    project_id = serializers.IntegerField()
    project_name = serializers.CharField()
    status = serializers.CharField()
    priority = serializers.CharField()
