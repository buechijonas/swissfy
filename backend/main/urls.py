from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/health/", views.health, name="health"),
    path("api/auth/", include("swissfy.accounts.urls")),
    path("api/social/", include("swissfy.social.urls")),
    path("api/chats/", include("swissfy.chats.urls")),
    path("api/", include("swissfy.posts.urls")),
    path("api/", include("swissfy.moderation.urls")),
    path("api/administration/", include("swissfy.accounts.administration_urls")),
    path("api/internal/", include("swissfy.accounts.internal_urls")),
    path("api/notifications/", include("swissfy.notifications.urls")),
    path("api/docs/", include("docs.urls")),
]
