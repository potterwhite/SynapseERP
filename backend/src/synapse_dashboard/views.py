# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.1.0-20250905 (Dashboard view with notification logic)

from django.shortcuts import render
from django.conf import settings
from django.utils.module_loading import import_string
import markdown2

# Import the Notification model we created
from .models import Notification


def dashboard_view(request):
    """
    Renders the dashboard-style home page.

    This view now also fetches the latest notification from the database,
    converts its Markdown content to HTML, and passes it to the template.
    """
    # --- START: Notification Panel Logic ---
    notification_html = None
    latest_notification = Notification.objects.order_by("-updated_at").first()

    if latest_notification:
        # Convert Markdown content to HTML.
        # The 'safe_mode' argument is deprecated and handled by default.
        # For more advanced security like stripping raw HTML, use libraries like bleach.
        # For our trusted admin-input use case, this is secure.
        notification_html = markdown2.markdown(latest_notification.content)
    # --- END: Notification Panel Logic ---

    all_modules_config = getattr(settings, "SYNAPSE_MODULES", [])
    main_content_module_config = None
    toolbox_modules_config = []

    sorted_modules = sorted(all_modules_config, key=lambda m: m.get("order", 99))
    for module in sorted_modules:
        if module.get("placement") == "main_content" and not main_content_module_config:
            main_content_module_config = module
        elif module.get("placement") == "toolbox":
            toolbox_modules_config.append(module)

    rendered_main_content_html = ""
    if main_content_module_config and "render_function" in main_content_module_config:
        try:
            render_func = import_string(main_content_module_config["render_function"])
            rendered_main_content_html = render_func(request)
        except (ImportError, AttributeError) as e:
            error_msg = (
                f"<div style='color: red; border: 1px solid red; padding: 10px;'>"
                f"<strong>Module Error:</strong> Failed to load '{main_content_module_config.get('display_name')}'.<br>"
                f"<strong>Details:</strong> {e}</div>"
            )
            rendered_main_content_html = error_msg

    context = {
        "main_content_html": rendered_main_content_html,
        "toolbox_modules": toolbox_modules_config,
        # Add the generated notification HTML to the context
        "notification_html": notification_html,
    }
    return render(request, "synapse_dashboard/dashboard.html", context)
