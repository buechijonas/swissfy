from django.urls import path

from .views import NotificationViewSet

urlpatterns = [
    path("", NotificationViewSet.as_view({"get": "list"}), name="notifications"),
    path(
        "unread/",
        NotificationViewSet.as_view({"get": "unread"}),
        name="notifications-unread",
    ),
    path(
        "read/",
        NotificationViewSet.as_view({"post": "mark_read"}),
        name="notifications-read",
    ),
]
