from django.urls import path

from .administration import AdminUserViewSet

urlpatterns = [
    path("roles/", AdminUserViewSet.as_view({"get": "roles"}), name="admin-roles"),
    path("users/", AdminUserViewSet.as_view({"get": "list"}), name="admin-users"),
    path(
        "users/<str:username>/",
        AdminUserViewSet.as_view({"patch": "partial_update"}),
        name="admin-user",
    ),
]
