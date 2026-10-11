from django.urls import path

from . import views

urlpatterns = [
    path("posts/<uuid:uuid>/report/", views.PostReportView.as_view(), name="post-report"),
    path("comments/<uuid:uuid>/report/", views.CommentReportView.as_view(), name="comment-report"),
    path("moderation/reports/", views.ReportQueueView.as_view(), name="moderation-reports"),
    path(
        "moderation/posts/<uuid:uuid>/", views.ModerationPostView.as_view(), name="moderation-post"
    ),
    path(
        "moderation/posts/<uuid:uuid>/comments/",
        views.ModerationPostCommentsView.as_view(),
        name="moderation-post-comments",
    ),
    path(
        "moderation/posts/<uuid:uuid>/warnings/",
        views.PostWarnView.as_view(),
        name="moderation-post-warn",
    ),
    path(
        "moderation/posts/<uuid:uuid>/dismiss/",
        views.PostDismissView.as_view(),
        name="moderation-post-dismiss",
    ),
    path(
        "moderation/comments/<uuid:uuid>/",
        views.ModerationCommentView.as_view(),
        name="moderation-comment",
    ),
    path(
        "moderation/comments/<uuid:uuid>/replies/",
        views.ModerationCommentRepliesView.as_view(),
        name="moderation-comment-replies",
    ),
    path(
        "moderation/comments/<uuid:uuid>/warnings/",
        views.CommentWarnView.as_view(),
        name="moderation-comment-warn",
    ),
    path(
        "moderation/comments/<uuid:uuid>/dismiss/",
        views.CommentDismissView.as_view(),
        name="moderation-comment-dismiss",
    ),
]
