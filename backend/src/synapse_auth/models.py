# Copyright (c) 2026 PotterWhite
# MIT License — see LICENSE in the project root.
#
# UserProfile extends Django's built-in User with role and tag-based access control.

from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """
    Extends Django's built-in User with Synapse-specific fields.

    Created automatically via post_save signal on User creation.
    Superusers always get role='admin' regardless of this field.

    Role semantics:
      admin  — full access to all projects, user management, sync config
      editor — read/write access to projects matching their allowed_tags
      viewer — read-only access to projects matching their allowed_tags

    Tag-based project access:
      - admin: sees ALL projects, ignores allowed_tags
      - editor/viewer: sees projects where project.tags is empty
                       OR at least one project tag is in allowed_tags
    """

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        EDITOR = "editor", "Editor"
        VIEWER = "viewer", "Viewer"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.VIEWER,
        help_text="User role: admin / editor / viewer",
    )
    # Tags this user is allowed to see. Empty list = no projects visible (unless admin).
    allowed_tags = models.JSONField(
        default=list,
        blank=True,
        help_text="List of project tags this user can access, e.g. ['work', 'urgent']",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self) -> str:
        return f"{self.user.username} ({self.role})"

    @property
    def effective_role(self) -> str:
        """Superusers are always treated as admin regardless of stored role."""
        if self.user.is_superuser:
            return self.Role.ADMIN
        return self.role

    def can_see_project(self, project_tags: list) -> bool:
        """
        Return True if this user can see a project with the given tags.

        Rules:
          - Admin (or superuser): always True
          - Others: True if project_tags is empty (untagged projects are visible to all)
                    OR any tag in project_tags is in self.allowed_tags
        """
        if self.effective_role == self.Role.ADMIN:
            return True
        if not project_tags:
            return True
        allowed = set(self.allowed_tags or [])
        return bool(allowed.intersection(project_tags))
