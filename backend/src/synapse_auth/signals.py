# Copyright (c) 2026 PotterWhite
# MIT License — see LICENSE in the project root.
#
# Auto-create UserProfile whenever a User is saved for the first time.

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance: User, created: bool, **kwargs):
    """
    Signal handler: ensure every User has a UserProfile.

    On creation:
      - Superusers automatically get role='admin'.
      - Regular users get the default role ('viewer').

    On update:
      - If the user was just promoted to is_superuser, upgrade their role to 'admin'.
    """
    if created:
        role = UserProfile.Role.ADMIN if instance.is_superuser else UserProfile.Role.VIEWER
        UserProfile.objects.create(user=instance, role=role)
    else:
        # Ensure profile exists (defensive, e.g. for legacy users)
        profile, _ = UserProfile.objects.get_or_create(user=instance)
        # Sync admin role if superuser flag changed
        if instance.is_superuser and profile.role != UserProfile.Role.ADMIN:
            profile.role = UserProfile.Role.ADMIN
            profile.save(update_fields=["role"])
