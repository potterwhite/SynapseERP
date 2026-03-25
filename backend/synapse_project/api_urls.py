# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# Root API URL configuration. All /api/* routes are registered here.
# Individual app API URLs are included via app-level api_urls.py files.

from django.urls import path, include

urlpatterns = [
    # synapse_api handles: GET /api/health/ and GET /api/dashboard/
    path("", include("synapse_api.urls")),
    # PM module: /api/pm/*
    path("pm/", include("synapse_pm.urls")),
    # Attendance Analyzer: /api/attendance/*
    path("attendance/", include("synapse_attendance.api_urls")),
    # BOM Analyzer: /api/bom/*
    path("bom/", include("synapse_bom_analyzer.api_urls")),
]
