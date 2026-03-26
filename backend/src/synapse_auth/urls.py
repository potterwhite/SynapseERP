# Copyright (c) 2026 PotterWhite
# MIT License — see LICENSE in the project root.
#
# URL patterns for the synapse_auth app.
# All routes are mounted under /api/auth/ via api_urls.py.

from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path("login/",    views.login_view,              name="auth-login"),
    path("logout/",   views.logout_view,             name="auth-logout"),
    path("refresh/",  views.CustomTokenRefreshView.as_view(), name="auth-refresh"),
    path("me/",       views.current_user,            name="auth-me"),
    path("register/", views.register_view,           name="auth-register"),

    # User management (admin only)
    path("users/",          views.user_list,   name="auth-user-list"),
    path("users/<int:pk>/", views.user_detail, name="auth-user-detail"),
]
