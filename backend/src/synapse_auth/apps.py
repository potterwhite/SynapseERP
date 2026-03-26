# Copyright (c) 2026 PotterWhite
# MIT License — see LICENSE in the project root.

from django.apps import AppConfig


class SynapseAuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "synapse_auth"
    verbose_name = "Synapse Auth"

    def ready(self):
        # Register signals (auto-create UserProfile on User save)
        import synapse_auth.signals  # noqa: F401
