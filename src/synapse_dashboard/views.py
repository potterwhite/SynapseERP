from django.shortcuts import render
from django.conf import settings
from django.utils.module_loading import import_string


def dashboard_view(request):
    """
    Renders the dashboard-style home page.
    """
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
    }
    return render(
        request, "synapse_dashboard/dashboard.html", context
    )  
