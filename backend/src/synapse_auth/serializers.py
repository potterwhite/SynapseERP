# Copyright (c) 2026 PotterWhite
# MIT License — see LICENSE in the project root.
#
# Serializers for authentication and user management.

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import UserProfile


# ---------------------------------------------------------------------------
# User serializers
# ---------------------------------------------------------------------------

class UserProfileSerializer(serializers.ModelSerializer):
    """Read-only serializer for the embedded profile in UserSerializer."""

    class Meta:
        model = UserProfile
        fields = ["role", "allowed_tags", "created_at"]
        read_only_fields = ["created_at"]


class UserSerializer(serializers.ModelSerializer):
    """
    Full user representation including profile.
    Used by GET /api/auth/me/ and GET /api/auth/users/{id}/.
    """

    role = serializers.CharField(source="profile.effective_role", read_only=True)
    allowed_tags = serializers.ListField(
        child=serializers.CharField(),
        source="profile.allowed_tags",
        read_only=True,
    )

    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "allowed_tags", "is_superuser"]
        read_only_fields = ["id", "is_superuser"]


class UserCreateSerializer(serializers.Serializer):
    """
    Used by POST /api/auth/users/ (admin creates a new user).
    """

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(
        choices=UserProfile.Role.choices,
        default=UserProfile.Role.VIEWER,
    )
    allowed_tags = serializers.ListField(
        child=serializers.CharField(),
        default=list,
        required=False,
    )

    def validate_username(self, value: str) -> str:
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def create(self, validated_data: dict) -> User:
        role = validated_data.pop("role")
        allowed_tags = validated_data.pop("allowed_tags", [])
        password = validated_data.pop("password")

        user = User.objects.create_user(password=password, **validated_data)

        # The signal creates a profile with default role; update it here
        user.profile.role = role
        user.profile.allowed_tags = allowed_tags
        user.profile.save(update_fields=["role", "allowed_tags"])

        return user


class UserUpdateSerializer(serializers.Serializer):
    """
    Used by PATCH /api/auth/users/{id}/ (admin updates role/tags).
    Intentionally does NOT allow password or username changes here.
    """

    role = serializers.ChoiceField(
        choices=UserProfile.Role.choices,
        required=False,
    )
    allowed_tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    email = serializers.EmailField(required=False)

    def update(self, instance: User, validated_data: dict) -> User:
        if "email" in validated_data:
            instance.email = validated_data["email"]
            instance.save(update_fields=["email"])

        profile = instance.profile
        if "role" in validated_data:
            profile.role = validated_data["role"]
        if "allowed_tags" in validated_data:
            profile.allowed_tags = validated_data["allowed_tags"]
        profile.save()

        return instance
