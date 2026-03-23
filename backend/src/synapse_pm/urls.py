from django.urls import path, include

urlpatterns = [
    # PM API endpoints registered in Step 2.5
    path("", include("synapse_pm.api.urls")),
]
