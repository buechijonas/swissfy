from django.urls import path

from . import views

urlpatterns = [
    path(
        "posts/<uuid:uuid>/report/",
        views.PostReportViewSet.as_view({"post": "report"}),
        name="post-report",
    ),
    path(
        "comments/<uuid:uuid>/report/",
        views.CommentReportViewSet.as_view({"post": "report"}),
        name="comment-report",
    ),
    path(
        "moderation/reports/",
        views.ReportQueueViewSet.as_view({"get": "list"}),
        name="moderation-reports",
    ),
    path(
        "moderation/posts/<uuid:uuid>/",
        views.ModerationPostViewSet.as_view({"get": "retrieve"}),
        name="moderation-post",
    ),
    path(
        "moderation/posts/<uuid:uuid>/comments/",
        views.ModerationPostCommentViewSet.as_view({"get": "list"}),
        name="moderation-post-comments",
    ),
    path(
        "moderation/posts/<uuid:uuid>/warnings/",
        views.PostModerationViewSet.as_view({"post": "warn"}),
        name="moderation-post-warn",
    ),
    path(
        "moderation/posts/<uuid:uuid>/dismiss/",
        views.PostModerationViewSet.as_view({"post": "dismiss"}),
        name="moderation-post-dismiss",
    ),
    path(
        "moderation/comments/<uuid:uuid>/",
        views.ModerationCommentViewSet.as_view({"get": "retrieve"}),
        name="moderation-comment",
    ),
    path(
        "moderation/comments/<uuid:uuid>/replies/",
        views.ModerationCommentReplyViewSet.as_view({"get": "list"}),
        name="moderation-comment-replies",
    ),
    path(
        "moderation/comments/<uuid:uuid>/warnings/",
        views.CommentModerationViewSet.as_view({"post": "warn"}),
        name="moderation-comment-warn",
    ),
    path(
        "moderation/comments/<uuid:uuid>/dismiss/",
        views.CommentModerationViewSet.as_view({"post": "dismiss"}),
        name="moderation-comment-dismiss",
    ),
]
