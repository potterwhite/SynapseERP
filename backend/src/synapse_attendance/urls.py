# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.1.0-20250905

from django.urls import path

# Import both the class-based view and the new function-based view
from .views import AnalysisView, download_report_view

app_name = "synapse_attendance"

urlpatterns = [
    # The existing URL for uploading and viewing the analysis
    path("analyze/", AnalysisView.as_view(), name="analyze"),
    # The new URL for handling download requests
    path("download/", download_report_view, name="download_report"),
]
