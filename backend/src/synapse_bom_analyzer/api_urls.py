from django.urls import path
from .api_views import api_analyze, api_download

urlpatterns = [
    path("analyze/", api_analyze, name="api-bom-analyze"),
    path("download/", api_download, name="api-bom-download"),
]
