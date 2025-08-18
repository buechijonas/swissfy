from django.urls import path

from root.views import AcceptFriendRequestView
from root.views import AccountView
from root.views import CancelFriendRequestView
from root.views import CreatePostView
from root.views import DeclineFriendRequestView
from root.views import DeletePostView
from root.views import DetailPostView
from root.views import DisclaimerView
from root.views import ForcePedoGuardView
from root.views import HomeView
from root.views import ImpressumView
from root.views import load_more_posts
from root.views import MaintenanceView
from root.views import NotificationAcitivitesView
from root.views import NotificationFriendRequestView
from root.views import NotificationView
from root.views import PedoGuardView
from root.views import PrivacyView
from root.views import ProfileFollowersView
from root.views import ProfileFollowingView
from root.views import ProfileFriendsView
from root.views import ProfileView
from root.views import RemoveFriendView
from root.views import SearchView
from root.views import SendFriendRequestView
from root.views import SettingsView
from root.views import SignUpView
from root.views import TermsView
from root.views import UpdateAccountLinksView
from root.views import UpdateAccountView
from root.views import UpdateCommentaryView
from root.views import UpdatePasswordSettingsView
from root.views import UpdatePostView
from root.views import UpdateSettingsView

from . import views


urlpatterns = [
    path("login/", views.sign_in, name="login"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("logout/", views.custom_logout, name="logout"),
    path("", HomeView.as_view(), name="home"),
    path("load-more-posts/", load_more_posts, name="load_more_posts"),
    path("post/<int:post_id>/like/", views.like_post, name="like_post"),
    path("search/", SearchView.as_view(), name="search"),
    path("notifications/", NotificationView.as_view(), name="notification"),
    path(
        "notifications/friend_requests/",
        NotificationFriendRequestView.as_view(),
        name="notification_friend_request",
    ),
    path(
        "notifications/activities/",
        NotificationAcitivitesView.as_view(),
        name="notification_activities",
    ),
    path("profile/<int:pk>/", ProfileView.as_view(), name="profile"),
    path(
        "profile/<int:pk>/friends", ProfileFriendsView.as_view(), name="profile_friends"
    ),
    path(
        "profile/<int:pk>/followers",
        ProfileFollowersView.as_view(),
        name="profile_followers",
    ),
    path(
        "profile/<int:pk>/following",
        ProfileFollowingView.as_view(),
        name="profile_following",
    ),
    path("account/", AccountView.as_view(), name="account"),
    path("account/<int:pk>/update", UpdateAccountView.as_view(), name="account_update"),
    path(
        "account/<int:pk>/links/update",
        UpdateAccountLinksView.as_view(),
        name="account_link_update",
    ),
    path("settings/", SettingsView.as_view(), name="settings"),
    path(
        "settings/<int:pk>/update", UpdateSettingsView.as_view(), name="settings_update"
    ),
    path(
        "settings/<int:pk>/pw/update",
        UpdatePasswordSettingsView.as_view(),
        name="settings_pw_update",
    ),
    path("follow/<int:user_id>/", views.follow_user, name="follow_user"),
    path("post/create", CreatePostView.as_view(), name="post_create"),
    path("post/<int:pk>", DetailPostView.as_view(), name="post"),
    path("post/<int:pk>/update", UpdatePostView.as_view(), name="post_update"),
    path("post/<int:pk>/delete", DeletePostView.as_view(), name="post_delete"),
    path("post/<int:pk>/comment/", views.commentary_create, name="commentary_create"),
    path(
        "commentary/<int:pk>/update",
        UpdateCommentaryView.as_view(),
        name="commentary_update",
    ),
    path(
        "notifications/accept/<int:pk>/",
        AcceptFriendRequestView.as_view(),
        name="accept_friend_request",
    ),
    path(
        "notifications/decline/<int:pk>/",
        DeclineFriendRequestView.as_view(),
        name="decline_friend_request",
    ),
    path(
        "send_request/<int:pk>/",
        SendFriendRequestView.as_view(),
        name="send_friend_request",
    ),
    path(
        "cancel_request/<int:pk>/",
        CancelFriendRequestView.as_view(),
        name="cancel_friend_request",
    ),
    path(
        "remove_friend/<int:pk>/",
        RemoveFriendView.as_view(),
        name="remove_friend",
    ),
    path("impressum/", ImpressumView.as_view(), name="impressum"),
    path("privacy/", PrivacyView.as_view(), name="privacy"),
    path("terms/", TermsView.as_view(), name="terms"),
    path("disclaimer/", DisclaimerView.as_view(), name="disclaimer"),
    path("pedoguard/", PedoGuardView.as_view(), name="pedoguard"),
    path("pedoguard/force", ForcePedoGuardView.as_view(), name="force_pedoguard"),
    path("503/", MaintenanceView.as_view(), name="maintenance"),
]
