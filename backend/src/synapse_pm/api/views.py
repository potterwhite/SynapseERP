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
from ..models import Project, Task, SyncMeta
from ..serializers import (
    GanttTaskSerializer,
    ProjectDetailSerializer,
    ProjectSerializer,
    ProjectWriteSerializer,
    TaskSerializer,
    TaskWriteSerializer,
    TimeEntryCreateSerializer,
    TimeEntrySerializer,
)


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def project_list(request: Request) -> Response:
    """
    GET  /api/pm/projects/
    POST /api/pm/projects/

    Query params (GET):
      status   — 'active' | 'archived' | 'on_hold' | 'all'
      search   — substring match on name / full_name
      ordering — 'name' | '-name' | 'deadline' | '-deadline'
    """
    adapter = get_adapter()

    if request.method == "POST":
        ser = ProjectWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data.copy()
        # Create project via ORM
        project = Project.objects.create(**data)
        result = adapter.get_project(project.pk)
        return Response(result, status=status.HTTP_201_CREATED)

    # GET
    raw_status = request.query_params.get("status", "active")
    filter_status = None if raw_status == "all" else raw_status

    # tags query param: comma-separated list of tags to filter by (AND semantics)
    raw_tags = request.query_params.get("tags", "").strip()
    filter_tags: list[str] | None = (
        [t.strip() for t in raw_tags.split(",") if t.strip()]
        if raw_tags
        else None
    )

    projects = adapter.list_projects(status=filter_status, tags=filter_tags)

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


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def project_detail(request: Request, project_id: int) -> Response:
    """
    GET   /api/pm/projects/{id}/
    PATCH /api/pm/projects/{id}/
    """
    adapter = get_adapter()

    if request.method == "PATCH":
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        ser = ProjectWriteSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        for field, value in ser.validated_data.items():
            setattr(project, field, value)
        project.save()
        result = adapter.get_project(project.pk)
        return Response(result)

    # GET
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


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def task_detail(request: Request, task_uuid: str) -> Response:
    """
    GET    /api/pm/tasks/{uuid}/
    PATCH  /api/pm/tasks/{uuid}/
    DELETE /api/pm/tasks/{uuid}/  (soft-delete: sets status to cancelled)
    """
    adapter = get_adapter()

    if request.method == "DELETE":
        task = adapter.update_task(task_uuid, {"status": "cancelled"})
        if task is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"detail": "Task cancelled.", "uuid": task_uuid})

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
        # In DB-Primary mode, time entries are always stored in DB only.
        # Vault sync is handled separately by the sync service.
        result = dict(entry, written_to_daily_note=False)
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
# Vault sync — status, trigger, and configuration
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sync_status(request: Request) -> Response:
    """
    GET /api/pm/sync/

    Returns current sync status: vault path, enabled flag, last sync timestamps,
    and current DB record counts.
    """
    from ..vault.sync_service import ObsidianSyncService
    svc = ObsidianSyncService()
    return Response(svc.get_status())


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sync_trigger(request: Request) -> Response:
    """
    POST /api/pm/sync/

    Triggers a vault sync operation.

    Request body (all optional):
      {
        "mode":    "import" | "export"   (default: "import")
        "full":    true | false           (default: false; import only)
        "dry_run": true | false           (default: false)
      }

    Response:
      {
        "status":                 "completed" | "disabled" | "error"
        "mode":                   "import" | "export"
        "projects_created":       int
        "projects_updated":       int
        "tasks_created":          int
        "tasks_updated":          int
        "time_entries_created":   int
        "skipped":                int
        "errors":                 list[str]
        "duration_ms":            int
      }
    """
    from ..vault.sync_service import ObsidianSyncService
    svc = ObsidianSyncService()

    if not svc.enabled:
        return Response(
            {
                "status": "disabled",
                "detail": (
                    "Vault sync is not enabled. "
                    "Configure vault_path via /api/pm/sync/config/ or set OBSIDIAN_VAULT_PATH in .env."
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    mode: str = request.data.get("mode", "import")
    full: bool = bool(request.data.get("full", False))
    dry_run: bool = bool(request.data.get("dry_run", False))

    t0 = time.monotonic()
    try:
        if mode == "export":
            result = svc.export_to_vault(dry_run=dry_run)
        else:
            result = svc.import_from_vault(full=full, dry_run=dry_run)
    except Exception as exc:
        return Response(
            {"status": "error", "detail": str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    duration_ms = int((time.monotonic() - t0) * 1000)

    return Response(
        {
            "status": "completed",
            "mode": mode,
            "dry_run": dry_run,
            "duration_ms": duration_ms,
            **result.to_dict(),
        }
    )


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def sync_config(request: Request) -> Response:
    """
    GET  /api/pm/sync/config/
    PATCH /api/pm/sync/config/

    Manage dynamic sync configuration stored in SyncMeta.

    GET response:
      {
        "vault_path":    str | null   (from SyncMeta, overrides .env)
        "env_vault_path": str | null  (from settings.OBSIDIAN_VAULT_PATH, read-only)
        "effective_vault_path": str | null  (the path actually used)
        "sync_enabled":  bool
      }

    PATCH request body:
      {
        "vault_path": "/absolute/path/to/vault"   (set to "" or null to clear)
      }
    """
    from ..vault.sync_service import ObsidianSyncService, get_vault_path

    if request.method == "PATCH":
        new_path = request.data.get("vault_path", "").strip()
        if new_path:
            # Validate directory exists
            import os
            if not os.path.isdir(new_path):
                return Response(
                    {"detail": f"Path does not exist or is not a directory: {new_path}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            SyncMeta.objects.update_or_create(
                key="vault_path",
                defaults={"value": new_path},
            )
        else:
            # Clear the dynamic vault_path — fall back to .env setting
            SyncMeta.objects.filter(key="vault_path").delete()

    # Build response for both GET and PATCH
    dynamic_path: str | None = None
    try:
        meta = SyncMeta.objects.get(key="vault_path")
        if meta.value.strip():
            dynamic_path = meta.value.strip()
    except SyncMeta.DoesNotExist:
        pass

    env_path = getattr(settings, "OBSIDIAN_VAULT_PATH", None) or None
    effective_path = dynamic_path or env_path

    svc = ObsidianSyncService()

    return Response({
        "vault_path": dynamic_path,
        "env_vault_path": env_path,
        "effective_vault_path": effective_path,
        "sync_enabled": svc.enabled,
    })


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tags_list(request: Request) -> Response:
    """
    GET /api/pm/tags/

    Return a sorted list of all distinct tags currently used by projects.
    This powers the tag-filter multi-select on the frontend.

    Response:
      { "tags": ["personal", "urgent", "work", ...] }
    """
    all_tags: set[str] = set()
    for project in Project.objects.only("tags"):
        for tag in (project.tags or []):
            if tag:
                all_tags.add(tag)
    return Response({"tags": sorted(all_tags)})
