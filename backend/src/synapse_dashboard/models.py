# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.1.0-20250905 (Notification model for Synapse Dashboard)

from django.db import models
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    """
    Stores notification messages to be displayed on the main dashboard.

    The content is stored in Markdown format and will be rendered as HTML
    in the view layer. The system is designed to display only the most
    recently updated notification.
    """

    content = models.TextField(
        verbose_name=_("Content"),
        help_text=_("The notification content in Markdown format."),
    )
    created_at = models.DateTimeField(
        verbose_name=_("Created At"),
        auto_now_add=True,
        help_text=_("The date and time this notification was created."),
    )
    updated_at = models.DateTimeField(
        verbose_name=_("Updated At"),
        auto_now=True,
        help_text=_("The date and time this notification was last updated."),
    )

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ["-updated_at"]

    def __str__(self):
        """
        Returns a truncated version of the content for display in the admin.
        """
        if len(self.content) > 75:
            return f"{self.content[:75]}..."
        return self.content
