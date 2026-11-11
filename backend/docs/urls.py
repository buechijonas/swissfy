from django.urls import path

from .views import ChangelogViewSet

urlpatterns = [
    path(
        "changelogs/",
        ChangelogViewSet.as_view({"get": "list"}),
        name="changelog-list",
    ),
    path(
        "changelogs/<str:version>/",
        ChangelogViewSet.as_view({"get": "retrieve"}),
        name="changelog-detail",
    ),
]
