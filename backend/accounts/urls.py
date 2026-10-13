from django.urls import path

from . import oidc, views

urlpatterns = [
    path("oidc/login/", oidc.govex_login, name="govex-login"),
    path("oidc/callback/", oidc.govex_callback, name="govex-callback"),
    path("oidc/account/", oidc.govex_account, name="govex-account"),
    path("oidc/account-deleted/", oidc.govex_account_deleted, name="govex-account-deleted"),
    path("oidc/account-updated/", oidc.govex_account_updated, name="govex-account-updated"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("me/", views.MeView.as_view(), name="me"),
    path("consent/<str:field>/", views.ConsentAcceptView.as_view(), name="consent-accept"),
]
