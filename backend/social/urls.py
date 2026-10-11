from django.urls import path

from moderation.views import StatusView

from . import views

urlpatterns = [
    path("profiles/", views.ProfileListView.as_view(), name="profile-list"),
    path("profiles/me/", views.ProfileView.as_view(), name="profile-me"),
    path("profiles/me/privacy/", views.PrivacyView.as_view(), name="profile-privacy"),
    path(
        "profiles/me/follow-requests/",
        views.FollowRequestListView.as_view(),
        name="profile-follow-requests",
    ),
    path(
        "profiles/me/follow-requests/<str:username>/",
        views.FollowRequestView.as_view(),
        name="profile-follow-request",
    ),
    path(
        "profiles/me/friend-requests/<str:username>/",
        views.FriendRequestDecisionView.as_view(),
        name="profile-friend-request-decision",
    ),
    path("profiles/<str:username>/", views.ProfileView.as_view(), name="profile"),
    path("profiles/<str:username>/status/", StatusView.as_view(), name="profile-status"),
    path("profiles/<str:username>/follow/", views.FollowView.as_view(), name="profile-follow"),
    path(
        "profiles/<str:username>/friend-request/",
        views.FriendRequestView.as_view(),
        name="profile-friend-request",
    ),
]
