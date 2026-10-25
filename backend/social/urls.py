from django.urls import path

from achievements.views import AchievementsView
from moderation.views import StatusView

from . import views

urlpatterns = [
    path("profiles/", views.ProfileListView.as_view(), name="profile-list"),
    path("profiles/me/", views.ProfileView.as_view(), name="profile-me"),
    path("profiles/me/privacy/", views.PrivacyView.as_view(), name="profile-privacy"),
    path("profiles/me/pictures/", views.PictureSettingsView.as_view(), name="profile-pictures"),
    path("profiles/me/about/", views.AboutView.as_view(), name="profile-about"),
    path("library/<str:kind>/", views.LibrarySearchView.as_view(), name="library-search"),
    path("covers/<path:path>", views.CoverView.as_view(), name="cover"),
    path(
        "profiles/me/pictures/<str:kind>/",
        views.OwnPictureView.as_view(),
        name="profile-own-picture",
    ),
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
    path(
        "profiles/<str:username>/pictures/<str:kind>/",
        views.PictureView.as_view(),
        name="profile-picture",
    ),
    path(
        "profiles/<str:username>/followers/",
        views.ConnectionListView.as_view(connections=views.followers_of),
        name="profile-followers",
    ),
    path(
        "profiles/<str:username>/following/",
        views.ConnectionListView.as_view(connections=views.followed_by),
        name="profile-following",
    ),
    path(
        "profiles/<str:username>/friends/",
        views.ConnectionListView.as_view(connections=views.friends_of),
        name="profile-friends",
    ),
    path("profiles/<str:username>/status/", StatusView.as_view(), name="profile-status"),
    path(
        "profiles/<str:username>/achievements/",
        AchievementsView.as_view(),
        name="profile-achievements",
    ),
    path("profiles/<str:username>/follow/", views.FollowView.as_view(), name="profile-follow"),
    path(
        "profiles/<str:username>/friend-request/",
        views.FriendRequestView.as_view(),
        name="profile-friend-request",
    ),
]
