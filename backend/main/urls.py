from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/health/", views.health, name="health"),
    path("api/auth/", include("accounts.urls")),
]
