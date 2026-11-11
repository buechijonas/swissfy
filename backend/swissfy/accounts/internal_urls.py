from django.urls import path

from .internal import InternalProfileViewSet

urlpatterns = [
    path(
        "profiles/<str:govex_sub>/",
        InternalProfileViewSet.as_view({"get": "retrieve"}),
        name="internal-profile",
    ),
    path(
        "profiles/<str:govex_sub>/picture/",
        InternalProfileViewSet.as_view({"get": "picture"}),
        name="internal-picture",
    ),
]
