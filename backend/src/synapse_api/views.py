from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint. No authentication required.
    Used by load balancers, Docker health checks, and frontend connectivity tests.

    GET /api/health/
    Response: {"status": "ok", "version": "...", "pm_backend": "...", "vault_connected": bool}
    """
    import os
    from synapse import __version__ as version

    pm_backend = getattr(settings, "SYNAPSE_PM_BACKEND", "database")
    vault_path = getattr(settings, "OBSIDIAN_VAULT_PATH", None)
    vault_connected = bool(vault_path and os.path.isdir(vault_path))

    payload: dict = {
        "status": "ok",
        "version": version,
        "pm_backend": pm_backend,
    }
    if pm_backend == "vault":
        payload["vault_connected"] = vault_connected
        payload["vault_path"] = vault_path

    return Response(payload)


@api_view(["GET"])
@permission_classes([AllowAny])
def dashboard(request):
    """
    Returns dashboard data: latest notification (raw Markdown) + toolbox modules.
    Markdown rendering is intentionally delegated to the frontend (markdown-it).

    GET /api/dashboard/
    Response:
    {
      "notification": "## Hello\\n\\nMarkdown content..." | null,
      "modules": [
        {"key": "attendance", "display_name": "...", "route": "/attendance", "description": "..."},
        ...
      ]
    }
    """
    # --- Notification ---
    # Import here to avoid circular imports if this module is loaded early
    from synapse_dashboard.models import Notification

    latest = Notification.objects.order_by("-updated_at").first()
    notification_content = latest.content if latest else None

    # --- Modules ---
    all_modules = getattr(settings, "SYNAPSE_MODULES", [])
    sorted_modules = sorted(all_modules, key=lambda m: m.get("order", 99))

    # Map app_name to a frontend route
    route_map: dict[str, str] = {
        "synapse_attendance": "/attendance",
        "synapse_bom_analyzer": "/bom",
        "synapse_pm": "/pm",
    }

    modules = [
        {
            "key": m["app_name"],
            "display_name": str(m.get("display_name", m["app_name"])),
            "route": route_map.get(m["app_name"], "/"),
            "description": str(m.get("description", "")),
        }
        for m in sorted_modules
        if m.get("placement") == "toolbox"
    ]

    return Response({"notification": notification_content, "modules": modules})
