from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from commons.exceptions import BadRequest
from commons.views import BaseViewSet
from main.pagination import NextPagePagination
from swissfy.accounts.roles import IsModerator
from swissfy.posts.models import Comment, Post
from swissfy.posts.serializers import PostModelSerializer
from swissfy.posts.views.comments import (
    CommentDetailViewSet,
    CommentReplyListViewSet,
    PostCommentListViewSet,
)

from .models import AlreadyWarned, Report
from .permissions import CanModerateAuthor, CanReportAuthor, CanViewWarnings, IsNotAuthor
from .reviews import moderation_context, report_groups
from .sanctions import issue_warning
from .serializers import (
    ModerationDetailsSerializer,
    ModerationStatusSerializer,
    ReportGroupSerializer,
    WarningModelSerializer,
)

User = get_user_model()


class ReportViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, IsNotAuthor, CanReportAuthor]
    lookup_field = "uuid"
    lookup_value_converter = "uuid"

    @action(detail=True, methods=["post"])
    def report(self, request, uuid):
        self.get_object().report_by(request.user)
        return Response({"reported": True})


class PostReportViewSet(ReportViewSet):
    def get_queryset(self):
        return Post.objects.apply_acl(self.request.user)


class CommentReportViewSet(ReportViewSet):
    def get_queryset(self):
        return Comment.objects.apply_acl(self.request.user)


class ReportQueueViewSet(BaseViewSet, mixins.ListModelMixin):
    permission_classes = [IsModerator]
    pagination_class = NextPagePagination

    def get_queryset(self):
        resolved = self.request.query_params.get("status") == "resolved"
        return Report.objects.queue(self.request.user, resolved)

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        context = moderation_context(request)
        groups = [
            ReportGroupSerializer.of(group)(group, context=context).data
            for group in report_groups(page, request.user)
        ]
        return self.get_paginated_response(groups)


MODERATOR_OF_AUTHOR = [IsModerator, CanModerateAuthor]


class ModerationActionsMixin:
    model = None

    def reported_target(self):
        reported = self.model.objects.filter(reports__isnull=False).distinct()
        target = get_object_or_404(reported, uuid=self.kwargs["uuid"])
        self.check_object_permissions(self.request, target)
        return target

    def details(self, target):
        return ModerationDetailsSerializer(target, context={"request": self.request}).data

    @action(
        detail=True, methods=["post"], url_path="warnings", permission_classes=MODERATOR_OF_AUTHOR
    )
    def warn(self, request, uuid):
        target = self.reported_target()
        serializer = WarningModelSerializer.write(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data["reason"]
        try:
            warning = issue_warning(target, request.user, reason)
        except AlreadyWarned:
            raise BadRequest("Dieser Inhalt wurde bereits verwarnt.")
        return Response(
            {"warning": WarningModelSerializer.read(warning).data, "report_count": 0},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], permission_classes=MODERATOR_OF_AUTHOR)
    def dismiss(self, request, uuid):
        self.reported_target().reports.resolve()
        return Response({"report_count": 0})


class ReportedPostViewSet(ModerationActionsMixin, BaseViewSet, mixins.RetrieveModelMixin):
    permission_classes = [IsModerator]
    lookup_field = "uuid"
    lookup_value_converter = "uuid"
    model = Post

    def get_queryset(self):
        return Post.objects.reported().with_details(self.request.user)

    def retrieve(self, request, *args, **kwargs):
        post = self.get_object()
        context = moderation_context(request)
        return Response(
            {"post": PostModelSerializer.read(post, context=context).data, **self.details(post)}
        )


class ReportedCommentViewSet(ModerationActionsMixin, CommentDetailViewSet):
    permission_classes = [IsModerator]
    lookup_value_converter = "uuid"
    model = Comment

    def get_queryset(self):
        return Comment.objects.on_reported_posts().with_details(self.request.user)

    def get_posts(self):
        return Post.objects.reported().with_details(self.request.user)

    def get_serializer_context(self):
        return moderation_context(self.request)

    def retrieve(self, request, *args, **kwargs):
        data = super().retrieve(request, *args, **kwargs).data
        return Response({**data, **self.details(self.get_object())})


class ReportedPostCommentViewSet(PostCommentListViewSet):
    permission_classes = [IsModerator]

    def comments(self):
        return Comment.objects.all()

    def get_post(self):
        posts = Post.objects.reported().with_details(self.request.user)
        return get_object_or_404(posts, uuid=self.kwargs["uuid"])

    def get_serializer_context(self):
        return moderation_context(self.request)


class ReportedCommentReplyViewSet(CommentReplyListViewSet):
    permission_classes = [IsModerator]

    def comments(self):
        return Comment.objects.all()

    def get_parent(self):
        comments = Comment.objects.on_reported_posts().with_details(self.request.user)
        return get_object_or_404(comments, uuid=self.kwargs["uuid"])

    def get_serializer_context(self):
        return moderation_context(self.request)


class StatusViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, CanViewWarnings]
    lookup_field = "username"

    def get_queryset(self):
        return User.objects.filter(is_active=True)

    @action(detail=True)
    def status(self, request, username):
        context = self.get_serializer_context()
        return Response(ModerationStatusSerializer(self.get_object(), context=context).data)
