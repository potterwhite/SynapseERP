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

import time
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from ..adapters import get_adapter
from ..models import Project, Task
from ..serializers import (
    GanttTaskSerializer,
    ProjectDetailSerializer,
    ProjectSerializer,
    TaskSerializer,
    TaskWriteSerializer,
    TimeEntryCreateSerializer,
    TimeEntrySerializer,
)


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def project_list(request: Request) -> Response:
    """
    GET /api/pm/projects/

    Query params:
      status   — 'active' | 'archived' | 'on_hold' | 'all'
      search   — substring match on name / full_name
      ordering — 'name' | '-name' | 'deadline' | '-deadline'
    """
    adapter = get_adapter()
    raw_status = request.query_params.get("status", "active")
    filter_status = None if raw_status == "all" else raw_status

    projects = adapter.list_projects(status=filter_status)

    # Additional in-memory filters (small data sets — no SQL needed yet)
    search = request.query_params.get("search", "").lower().strip()
    if search:
        projects = [
            p for p in projects
            if search in p["name"].lower() or search in p["full_name"].lower()
        ]

    ordering = request.query_params.get("ordering", "name")
    reverse = ordering.startswith("-")
    key = ordering.lstrip("-")
    if key in ("name", "deadline", "created"):
        projects.sort(key=lambda p: (p.get(key) or ""), reverse=reverse)

    # Pagination
    page = int(request.query_params.get("page", 1))
    page_size = min(int(request.query_params.get("page_size", 20)), 100)
    total = len(projects)
    start = (page - 1) * page_size
    end = start + page_size
    page_data = projects[start:end]

    return Response({
        "count": total,
        "next": f"?page={page + 1}" if end < total else None,
        "previous": f"?page={page - 1}" if page > 1 else None,
        "results": page_data,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def project_detail(request: Request, project_id: int) -> Response:
    """GET /api/pm/projects/{id}/"""
    adapter = get_adapter()
    project = adapter.get_project(project_id)
    if project is None:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    # Attach task list
    tasks = adapter.list_tasks(project_id=project_id)
    project["tasks"] = tasks
    return Response(project)


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def task_list(request: Request) -> Response:
    """
    GET  /api/pm/tasks/
    POST /api/pm/tasks/
    """
    adapter = get_adapter()

    if request.method == "POST":
        ser = TaskWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data.copy()
        data["depends_on"] = [str(u) for u in data.get("depends_on", [])]
        task = adapter.create_task(data)
        return Response(task, status=status.HTTP_201_CREATED)

    # GET
    project_id = request.query_params.get("project")
    filter_status = request.query_params.get("status")
    filter_priority = request.query_params.get("priority")

    tasks = adapter.list_tasks(
        project_id=int(project_id) if project_id else None,
        status=filter_status,
        priority=filter_priority,
    )

    search = request.query_params.get("search", "").lower().strip()
    if search:
        tasks = [t for t in tasks if search in t["name"].lower()]

    page = int(request.query_params.get("page", 1))
    page_size = min(int(request.query_params.get("page_size", 20)), 100)
    total = len(tasks)
    start = (page - 1) * page_size

    return Response({
        "count": total,
        "next": None,
        "previous": None,
        "results": tasks[start: start + page_size],
    })


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def task_detail(request: Request, task_uuid: str) -> Response:
    """
    GET   /api/pm/tasks/{uuid}/
    PATCH /api/pm/tasks/{uuid}/
    """
    adapter = get_adapter()

    if request.method == "PATCH":
        ser = TaskWriteSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data.copy()
        if "depends_on" in data:
            data["depends_on"] = [str(u) for u in data["depends_on"]]
        task = adapter.update_task(task_uuid, data)
        if task is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(task)

    # GET
    task = adapter.get_task(task_uuid)
    if task is None:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(task)


# ---------------------------------------------------------------------------
# Time Entries
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def time_entry_list(request: Request) -> Response:
    """
    GET  /api/pm/time-entries/?task_uuid=xxx
    POST /api/pm/time-entries/
    """
    adapter = get_adapter()

    if request.method == "POST":
        ser = TimeEntryCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data.copy()
        data["task_uuid"] = str(data["task_uuid"])
        data["date"] = data["date"].isoformat() if hasattr(data["date"], "isoformat") else data["date"]
        entry = adapter.create_time_entry(data)
        written = getattr(settings, "SYNAPSE_PM_BACKEND", "database") == "vault"
        result = dict(entry, written_to_daily_note=written)
        return Response(result, status=status.HTTP_201_CREATED)

    # GET
    task_uuid = request.query_params.get("task_uuid")
    if not task_uuid:
        return Response(
            {"detail": "task_uuid query parameter is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    entries = adapter.list_time_entries(task_uuid=task_uuid)
    return Response(entries)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pm_stats(request: Request) -> Response:
    """GET /api/pm/stats/"""
    adapter = get_adapter()
    return Response(adapter.get_stats())


# ---------------------------------------------------------------------------
# Gantt
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def gantt_tasks(request: Request) -> Response:
    """GET /api/pm/gantt/?project={id}"""
    adapter = get_adapter()
    project_id = request.query_params.get("project")
    tasks = adapter.list_gantt_tasks(
        project_id=int(project_id) if project_id else None
    )
    return Response({"tasks": tasks})


# ---------------------------------------------------------------------------
# Vault sync trigger
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sync_vault(request: Request) -> Response:
    """
    POST /api/pm/sync/

    Triggers the sync_vault management command programmatically.
    Only meaningful when SYNAPSE_PM_BACKEND = 'vault'.
    """
    backend = getattr(settings, "SYNAPSE_PM_BACKEND", "database")
    if backend != "vault":
        return Response(
            {"detail": "Vault sync is not available in database mode."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from django.core.management import call_command
    from io import StringIO

    t0 = time.monotonic()
    out = StringIO()
    try:
        call_command("sync_vault", stdout=out)
    except Exception as exc:
        return Response(
            {"detail": f"Sync failed: {exc}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    duration_ms = int((time.monotonic() - t0) * 1000)
    output = out.getvalue()

    # Parse counts from command output
    def _extract(label: str) -> int:
        import re
        m = re.search(rf"{label}\s*:\s*(\d+) created", output)
        return int(m.group(1)) if m else 0

    return Response({
        "status": "completed",
        "projects_synced": _extract("Projects"),
        "tasks_synced": _extract("Tasks"),
        "time_entries_synced": _extract("TimeEntries"),
        "duration_ms": duration_ms,
    })
