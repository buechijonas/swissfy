from django.urls import path

from commons.routers import Router

from . import oidc
from .views import AuthViewSet

router = Router()
router.register("", AuthViewSet, basename="auth")

urlpatterns = [
    path("oidc/login/", oidc.govex_login, name="govex-login"),
    path("oidc/callback/", oidc.govex_callback, name="govex-callback"),
    path("oidc/account/", oidc.govex_account, name="govex-account"),
    path("oidc/account-deleted/", oidc.govex_account_deleted, name="govex-account-deleted"),
    path("oidc/account-updated/", oidc.govex_account_updated, name="govex-account-updated"),
] + router.urls
