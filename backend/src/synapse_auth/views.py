# Copyright (c) 2026 PotterWhite
# MIT License — see LICENSE in the project root.
#
# Authentication views: login, logout, token refresh, current user, user CRUD.

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import UserProfile
from .permissions import IsAdminRole
from .serializers import UserCreateSerializer, UserRegisterSerializer, UserSerializer, UserUpdateSerializer


# ---------------------------------------------------------------------------
# Self-registration (public)
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request: Request) -> Response:
    """
    POST /api/auth/register/

    Public self-registration endpoint.  Anyone can create an account.
    New users are always assigned role='viewer' with no allowed_tags.
    Admins can later promote them via PATCH /api/auth/users/{id}/.

    Request body:
      { "username": "bob", "email": "bob@example.com",
        "password": "s3cr3t!!", "password_confirm": "s3cr3t!!" }

    Response 201:
      {
        "access":  "<jwt-access-token>",
        "refresh": "<jwt-refresh-token>",
        "user": { "id": 2, "username": "bob", "email": "bob@example.com",
                  "role": "viewer", "allowed_tags": [] }
      }

    Response 400: validation errors (username taken, password mismatch, etc.)
    """
    ser = UserRegisterSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    user = ser.save()

    # Issue JWT tokens immediately so the user is logged in after registration
    refresh = RefreshToken.for_user(user)
    return Response(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        },
        status=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------------------------
# Login / Logout / Refresh
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request: Request) -> Response:
    """
    POST /api/auth/login/

    Authenticate with username + password.  Returns JWT access + refresh tokens
    plus the user's profile (id, username, email, role, allowed_tags).

    Request body:
      { "username": "alice", "password": "s3cr3t" }

    Response 200:
      {
        "access":  "<jwt-access-token>",
        "refresh": "<jwt-refresh-token>",
        "user": { "id": 1, "username": "alice", "email": "", "role": "admin", "allowed_tags": [] }
      }

    Response 401:
      { "detail": "Invalid credentials." }
    """
    from django.contrib.auth import authenticate

    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")

    if not username or not password:
        return Response(
            {"detail": "Username and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(request=request, username=username, password=password)
    if user is None:
        return Response(
            {"detail": "Invalid credentials."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Ensure profile exists (defensive for legacy/admin users created before Phase 5.7)
    UserProfile.objects.get_or_create(
        user=user,
        defaults={"role": UserProfile.Role.ADMIN if user.is_superuser else UserProfile.Role.VIEWER},
    )

    refresh = RefreshToken.for_user(user)
    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": UserSerializer(user).data,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request: Request) -> Response:
    """
    POST /api/auth/logout/

    Blacklist the provided refresh token so it cannot be reused.

    Request body:
      { "refresh": "<refresh-token>" }

    Response 200:
      { "detail": "Successfully logged out." }
    """
    refresh_token = request.data.get("refresh")
    if not refresh_token:
        return Response(
            {"detail": "Refresh token is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except (TokenError, InvalidToken):
        # Token already invalid — treat as successful logout
        pass

    return Response({"detail": "Successfully logged out."})


class CustomTokenRefreshView(TokenRefreshView):
    """
    POST /api/auth/refresh/

    Thin wrapper around simplejwt's TokenRefreshView.
    Rotates the refresh token (ROTATE_REFRESH_TOKENS = True) and returns a new access token.

    Request body:
      { "refresh": "<refresh-token>" }

    Response 200:
      { "access": "<new-access-token>", "refresh": "<new-refresh-token>" }
    """
    pass


# ---------------------------------------------------------------------------
# Current user
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request: Request) -> Response:
    """
    GET /api/auth/me/

    Return the authenticated user's full profile.

    Response 200:
      { "id": 1, "username": "alice", "email": "", "role": "admin",
        "allowed_tags": [], "is_superuser": true }
    """
    # Ensure profile exists (defensive)
    UserProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "role": (
                UserProfile.Role.ADMIN
                if request.user.is_superuser
                else UserProfile.Role.VIEWER
            )
        },
    )
    return Response(UserSerializer(request.user).data)


# ---------------------------------------------------------------------------
# User management (admin only)
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminRole])
def user_list(request: Request) -> Response:
    """
    GET  /api/auth/users/  — list all users (admin only)
    POST /api/auth/users/  — create a new user (admin only)
    """
    if request.method == "POST":
        ser = UserCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    # GET
    users = User.objects.select_related("profile").order_by("id")
    return Response(UserSerializer(users, many=True).data)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, IsAdminRole])
def user_detail(request: Request, pk: int) -> Response:
    """
    GET    /api/auth/users/{id}/  — user detail (admin only)
    PATCH  /api/auth/users/{id}/  — update role / allowed_tags / email (admin only)
    DELETE /api/auth/users/{id}/  — delete user (admin only)
    """
    try:
        user = User.objects.select_related("profile").get(pk=pk)
    except User.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "DELETE":
        if user == request.user:
            return Response(
                {"detail": "You cannot delete your own account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    if request.method == "PATCH":
        ser = UserUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.update(user, ser.validated_data)
        user.refresh_from_db()
        return Response(UserSerializer(user).data)

    # GET
    return Response(UserSerializer(user).data)
