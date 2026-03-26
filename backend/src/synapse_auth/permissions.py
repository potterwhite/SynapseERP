# Copyright (c) 2026 PotterWhite
# MIT License — see LICENSE in the project root.
#
# Role-based permission classes for DRF views.

from rest_framework.permissions import BasePermission

from .models import UserProfile


class IsAdminRole(BasePermission):
    """
    Allows access only to users whose effective role is 'admin'
    (i.e. is_superuser OR profile.role == 'admin').
    """

    message = "Admin role required."

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        try:
            return request.user.profile.effective_role == UserProfile.Role.ADMIN
        except UserProfile.DoesNotExist:
            return False


class IsEditorOrAbove(BasePermission):
    """
    Allows access to users whose effective role is 'admin' or 'editor'.
    Viewers are denied write operations.
    """

    message = "Editor or Admin role required."

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        try:
            role = request.user.profile.effective_role
            return role in (UserProfile.Role.ADMIN, UserProfile.Role.EDITOR)
        except UserProfile.DoesNotExist:
            return False
