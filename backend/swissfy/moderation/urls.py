from commons.routers import Router

from . import views

router = Router()
router.register("posts", views.PostReportViewSet, basename="post-report")
router.register("comments", views.CommentReportViewSet, basename="comment-report")
router.register("moderation/reports", views.ReportQueueViewSet, basename="moderation-reports")
router.register(
    "moderation/posts/<uuid:uuid>/comments",
    views.ReportedPostCommentViewSet,
    basename="moderation-post-comments",
)
router.register(
    "moderation/comments/<uuid:uuid>/replies",
    views.ReportedCommentReplyViewSet,
    basename="moderation-comment-replies",
)
router.register("moderation/posts", views.ReportedPostViewSet, basename="moderation-post")
router.register("moderation/comments", views.ReportedCommentViewSet, basename="moderation-comment")

urlpatterns = router.urls
