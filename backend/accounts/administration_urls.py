from django.urls import path

from . import administration

urlpatterns = [
    path("roles/", administration.AdminRoleView.as_view(), name="admin-roles"),
    path("users/", administration.AdminUserListView.as_view(), name="admin-users"),
    path("users/<str:username>/", administration.AdminUserView.as_view(), name="admin-user"),
]
