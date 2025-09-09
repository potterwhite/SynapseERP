# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.1.0-20250905 (Admin registration for Notification model)

from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin interface options for the Notification model.

    This configuration improves the usability of the Notification model
    in the Django admin panel by specifying which fields to display
    in the list view and which fields can be used for searching.
    """

    list_display = ("__str__", "updated_at", "created_at")
    search_fields = ("content",)
    list_filter = ("updated_at",)
    readonly_fields = ("created_at", "updated_at")
