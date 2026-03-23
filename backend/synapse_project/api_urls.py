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
    # Health check — no authentication required
    path("health/", include("synapse_api.urls")),
]
