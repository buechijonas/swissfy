from django.urls import path

from . import views

urlpatterns = [
    path("profiles/", views.ProfileListView.as_view(), name="profile-list"),
    path("profiles/me/", views.ProfileView.as_view(), name="profile-me"),
    path("profiles/me/privacy/", views.PrivacyView.as_view(), name="profile-privacy"),
    path("profiles/<str:username>/", views.ProfileView.as_view(), name="profile"),
    path("profiles/<str:username>/follow/", views.FollowView.as_view(), name="profile-follow"),
    path(
        "profiles/<str:username>/friend-request/",
        views.FriendRequestView.as_view(),
        name="profile-friend-request",
    ),
]
