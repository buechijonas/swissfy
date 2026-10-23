from django.urls import path

from . import internal

urlpatterns = [
    path("profiles/<str:govex_sub>/", internal.InternalProfileView.as_view(), name="internal-profile"),
    path(
        "profiles/<str:govex_sub>/picture/",
        internal.InternalPictureView.as_view(),
        name="internal-picture",
    ),
]
