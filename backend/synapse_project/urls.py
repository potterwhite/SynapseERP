# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.9.0 (Root URL configuration for SynapseERP — Vue SPA era)
#
# After Phase 4 migration, all user-facing pages are served by the Vue SPA.
# Django only exposes:
#   /admin/          — Django admin interface
#   /api/            — REST API (DRF)
#   /i18n/           — Django internationalisation helper (set_language)
#
# Legacy Django template routes for attendance/, bom/, and the dashboard root
# have been removed.  In production, Nginx serves frontend/dist/ directly and
# forwards /api/, /admin/, /i18n/ to Gunicorn.  In development, the Vite proxy
# handles /api/* and everything else is served by the Vite dev server.

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django internationalisation: required for set_language cookie helper.
    path('i18n/', include('django.conf.urls.i18n')),

    # Django admin interface.
    path('admin/', admin.site.urls),

    # REST API: all /api/* routes are handled by api_urls.py.
    path('api/', include('synapse_project.api_urls')),
]
