from django.urls import path

from root.views import (
    DisclaimerView,
    HomeView,
    ImpressumView,
    PrivacyView,
    SignUpView,
    TermsView,
)

from . import views

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("login/", views.sign_in, name="login"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("logout/", views.custom_logout, name="logout"),
    path("impressum/", ImpressumView.as_view(), name="impressum"),
    path("privacy/", PrivacyView.as_view(), name="privacy"),
    path("terms/", TermsView.as_view(), name="terms"),
    path("disclaimer/", DisclaimerView.as_view(), name="disclaimer"),
]
