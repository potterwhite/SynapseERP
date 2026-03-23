from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health_check, name="health_check"),
    path("dashboard/", views.dashboard, name="dashboard"),
    # Current-user endpoint used by the frontend auth store on app boot.
    # Returns the logged-in user's id/username/email, or 403 if unauthenticated.
    path("auth/me/", views.current_user, name="current_user"),
]
