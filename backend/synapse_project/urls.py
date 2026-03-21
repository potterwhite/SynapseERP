# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.8.0-20250910 (Root URL configuration for SynapseERP)

from django.contrib import admin
from django.urls import path, include

# This urlpatterns list is the main entry point for all URL routing.
# It delegates specific paths to the individual application's urls.py files.
urlpatterns = [
    # NEW: Add Django's built-in internationalization URLs.
    # This provides the 'set_language' view required by the language switcher.
    path('i18n/', include('django.conf.urls.i18n')),

    # 1. Admin Interface: Provides the backend management site.
    path('admin/', admin.site.urls),

    # 2. Attendance Analyzer App: Routes all URLs starting with 'attendance/'
    #    to the synapse_attendance app's urls.py.
    #    e.g., /attendance/analyze/
    path('attendance/', include('synapse_attendance.urls', namespace='synapse_attendance')),

    # 3. BOM Analyzer App: Routes all URLs starting with 'bom/'
    #    to the synapse_bom_analyzer app's urls.py.
    #    e.g., /bom/
    path('bom/', include('synapse_bom_analyzer.urls', namespace='synapse_bom_analyzer')),
    
    # 4. Dashboard App: Routes the root URL ('/') to the dashboard.
    #    This should be the LAST entry for catch-all paths.
    path('', include('synapse_dashboard.urls', namespace='synapse_dashboard')),
]
