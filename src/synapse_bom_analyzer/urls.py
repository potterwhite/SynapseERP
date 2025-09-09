# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.1.0-20250905 (URL configuration for BOM Analyzer)

from django.urls import path
from . import views

app_name = "synapse_bom_analyzer"

urlpatterns = [
    # CORRECTED: Changed 'views.bom_upload_view' to 'views.analysis_view'
    # CORRECTED: Changed name='upload' to name='analyze' for consistency
    path("", views.analysis_view, name="analyze"),
    # This line is already correct
    path("download/", views.download_report_view, name="download_report"),
]
