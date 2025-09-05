# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.1.0-20250905

from django.urls import path
from .views import AnalysisView

# Define the app_name for URL namespacing.
# This allows us to use 'attendance:analyze' in templates.
app_name = 'synapse_attendance'

urlpatterns = [
    path('analyze/', AnalysisView.as_view(), name='analyze'),
]
