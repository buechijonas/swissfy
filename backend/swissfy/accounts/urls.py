from django.urls import path

from . import oidc
from .views import AuthViewSet

urlpatterns = [
    path("oidc/login/", oidc.govex_login, name="govex-login"),
    path("oidc/callback/", oidc.govex_callback, name="govex-callback"),
    path("oidc/account/", oidc.govex_account, name="govex-account"),
    path("oidc/account-deleted/", oidc.govex_account_deleted, name="govex-account-deleted"),
    path("oidc/account-updated/", oidc.govex_account_updated, name="govex-account-updated"),
    path("logout/", AuthViewSet.as_view({"post": "logout"}), name="logout"),
    path(
        "device/",
        AuthViewSet.as_view({"post": "sync_device", "delete": "forget_device"}),
        name="device-token",
    ),
    path(
        "device/restore/",
        AuthViewSet.as_view({"post": "restore_device"}),
        name="device-restore",
    ),
    path("me/", AuthViewSet.as_view({"get": "me"}), name="me"),
    path(
        "consent/<str:field>/",
        AuthViewSet.as_view({"post": "accept_consent"}),
        name="consent-accept",
    ),
]
