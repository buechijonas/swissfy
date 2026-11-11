from django.urls import path

from swissfy.achievements.views import AchievementViewSet
from swissfy.moderation.views import StatusViewSet

from .views import LibraryViewSet, OwnPictureViewSet, OwnProfileViewSet, ProfileViewSet

urlpatterns = [
    path("profiles/", ProfileViewSet.as_view({"get": "list"}), name="profile-list"),
    path("profiles/me/", ProfileViewSet.as_view({"get": "me"}), name="profile-me"),
    path(
        "profiles/me/privacy/",
        OwnProfileViewSet.as_view({"get": "privacy", "patch": "update_privacy"}),
        name="profile-privacy",
    ),
    path(
        "profiles/me/pictures/",
        OwnPictureViewSet.as_view({"get": "pictures", "patch": "update_pictures"}),
        name="profile-pictures",
    ),
    path(
        "profiles/me/about/",
        OwnProfileViewSet.as_view({"get": "about", "patch": "update_about"}),
        name="profile-about",
    ),
    path(
        "library/<str:kind>/",
        LibraryViewSet.as_view({"get": "search"}),
        name="library-search",
    ),
    path("covers/<path:path>", LibraryViewSet.as_view({"get": "cover"}), name="cover"),
    path(
        "profiles/me/pictures/<str:kind>/",
        OwnPictureViewSet.as_view({"delete": "delete_picture"}),
        name="profile-own-picture",
    ),
    path(
        "profiles/me/follow-requests/",
        OwnProfileViewSet.as_view({"get": "follow_requests"}),
        name="profile-follow-requests",
    ),
    path(
        "profiles/me/follow-requests/<str:username>/",
        OwnProfileViewSet.as_view(
            {"post": "decide_follow_request", "delete": "decide_follow_request"}
        ),
        name="profile-follow-request",
    ),
    path(
        "profiles/me/friend-requests/<str:username>/",
        OwnProfileViewSet.as_view(
            {"post": "decide_friend_request", "delete": "decide_friend_request"}
        ),
        name="profile-friend-request-decision",
    ),
    path(
        "profiles/<str:username>/",
        ProfileViewSet.as_view({"get": "retrieve"}),
        name="profile",
    ),
    path(
        "profiles/<str:username>/pictures/<str:kind>/",
        ProfileViewSet.as_view({"get": "picture"}),
        name="profile-picture",
    ),
    path(
        "profiles/<str:username>/followers/",
        ProfileViewSet.as_view({"get": "connections"}),
        {"kind": "followers"},
        name="profile-followers",
    ),
    path(
        "profiles/<str:username>/following/",
        ProfileViewSet.as_view({"get": "connections"}),
        {"kind": "following"},
        name="profile-following",
    ),
    path(
        "profiles/<str:username>/friends/",
        ProfileViewSet.as_view({"get": "connections"}),
        {"kind": "friends"},
        name="profile-friends",
    ),
    path(
        "profiles/<str:username>/status/",
        StatusViewSet.as_view({"get": "retrieve"}),
        name="profile-status",
    ),
    path(
        "profiles/<str:username>/achievements/",
        AchievementViewSet.as_view({"get": "retrieve"}),
        name="profile-achievements",
    ),
    path(
        "profiles/<str:username>/follow/",
        ProfileViewSet.as_view({"post": "follow", "delete": "unfollow"}),
        name="profile-follow",
    ),
    path(
        "profiles/<str:username>/friend-request/",
        ProfileViewSet.as_view({"post": "friend_request"}),
        name="profile-friend-request",
    ),
]
