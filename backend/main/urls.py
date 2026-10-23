from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/health/", views.health, name="health"),
    path("api/auth/", include("accounts.urls")),
    path("api/social/", include("social.urls")),
    path("api/chats/", include("chats.urls")),
    path("api/", include("posts.urls")),
    path("api/", include("moderation.urls")),
    path("api/administration/", include("accounts.administration_urls")),
    path("api/internal/", include("accounts.internal_urls")),
    path("api/notifications/", include("notifications.urls")),
]
