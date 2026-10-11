from django.urls import path

from . import views

urlpatterns = [
    path("", views.NotificationListView.as_view(), name="notifications"),
    path("unread/", views.UnreadCountView.as_view(), name="notifications-unread"),
    path("read/", views.ReadView.as_view(), name="notifications-read"),
]
