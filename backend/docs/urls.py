from django.urls import path

from . import views

urlpatterns = [
    path("changelogs/", views.ChangelogListView.as_view(), name="changelog-list"),
    path(
        "changelogs/<str:version>/",
        views.ChangelogView.as_view(),
        name="changelog-detail",
    ),
]
