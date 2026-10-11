from django.urls import path

from . import views

urlpatterns = [
    path("posts/", views.FeedView.as_view(), name="feed"),
    path("posts/quota/", views.PostQuotaView.as_view(), name="post-quota"),
    path("posts/saved/", views.SavedListView.as_view(), name="saved-posts"),
    path("posts/folders/", views.FolderListView.as_view(), name="saved-folders"),
    path("posts/folders/<int:pk>/", views.FolderDetailView.as_view(), name="saved-folder"),
    path("posts/groups/", views.GroupListView.as_view(), name="contact-groups"),
    path("posts/groups/<int:pk>/", views.GroupDetailView.as_view(), name="contact-group"),
    path("posts/users/<str:username>/", views.UserPostListView.as_view(), name="user-posts"),
    path(
        "posts/users/<str:username>/activities/",
        views.ActivityView.as_view(),
        name="user-activities",
    ),
    path("posts/<uuid:uuid>/", views.PostDetailView.as_view(), name="post"),
    path(
        "posts/<uuid:uuid>/images/<int:position>/",
        views.PostImageView.as_view(),
        name="post-image",
    ),
    path("posts/<uuid:uuid>/thumbnail/", views.PostThumbnailView.as_view(), name="post-thumbnail"),
    path("posts/<uuid:uuid>/like/", views.LikeView.as_view(), name="post-like"),
    path("posts/<uuid:uuid>/save/", views.SaveView.as_view(), name="post-save"),
    path("posts/<uuid:uuid>/comments/", views.CommentListView.as_view(), name="post-comments"),
    path("comments/<uuid:uuid>/", views.CommentDetailView.as_view(), name="comment"),
    path("comments/<uuid:uuid>/vote/", views.CommentVoteView.as_view(), name="comment-vote"),
    path(
        "comments/<uuid:uuid>/replies/",
        views.CommentReplyListView.as_view(),
        name="comment-replies",
    ),
]
