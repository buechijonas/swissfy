from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from commons.views import BaseViewSet
from main.pagination import NextPagePagination
from swissfy.accounts.roles import IsModerator
from swissfy.posts.models import Comment, Post
from swissfy.posts.serializers import PostModelSerializer
from swissfy.posts.views.comments import CommentReplyViewSet, CommentViewSet, PostCommentViewSet

from .models import Report, Warning
from .permissions import CanModerateAuthor, CanReportAuthor, CanViewWarnings, IsNotAuthor
from .reviews import ReportQueuePage, moderation_context, moderation_details, status_of
from .sanctions import issue_warning
from .serializers import WarningModelSerializer

User = get_user_model()


class ReportViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, IsNotAuthor, CanReportAuthor]
    lookup_field = "uuid"
    field = None

    def report(self, request, uuid):
        Report.objects.get_or_create(reporter=request.user, **{self.field: self.get_object()})
        return Response({"reported": True})


class PostReportViewSet(ReportViewSet):
    field = "post"

    def get_queryset(self):
        return Post.objects.apply_acl(self.request.user)


class CommentReportViewSet(ReportViewSet):
    field = "comment"

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
        return self.get_paginated_response(ReportQueuePage(page, request).results())


class ModerationPostViewSet(BaseViewSet, mixins.RetrieveModelMixin):
    permission_classes = [IsModerator]
    lookup_field = "uuid"

    def get_queryset(self):
        return Post.objects.reported().with_details(self.request.user)

    def retrieve(self, request, *args, **kwargs):
        post = self.get_object()
        return Response(
            {
                "post": PostModelSerializer.read(post, context=moderation_context(request)).data,
                **moderation_details(request.user, post, post=post),
            }
        )


class ModerationPostCommentViewSet(PostCommentViewSet):
    permission_classes = [IsModerator]

    def comments(self):
        return Comment.objects.all()

    def get_post(self):
        posts = Post.objects.reported().with_details(self.request.user)
        return get_object_or_404(posts, uuid=self.kwargs["uuid"])

    def get_serializer_context(self):
        return moderation_context(self.request)


class ModerationCommentReplyViewSet(CommentReplyViewSet):
    permission_classes = [IsModerator]

    def comments(self):
        return Comment.objects.all()

    def get_parent(self):
        comments = Comment.objects.on_reported_posts().with_details(self.request.user)
        return get_object_or_404(comments, uuid=self.kwargs["uuid"])

    def get_serializer_context(self):
        return moderation_context(self.request)


class ModerationCommentViewSet(CommentViewSet):
    permission_classes = [IsModerator]

    def get_queryset(self):
        return Comment.objects.on_reported_posts().with_details(self.request.user)

    def get_posts(self):
        return Post.objects.reported().with_details(self.request.user)

    def get_object(self):
        return get_object_or_404(self.get_queryset(), uuid=self.kwargs["uuid"])

    def get_serializer_context(self):
        return moderation_context(self.request)

    def retrieve(self, request, *args, **kwargs):
        comment = self.get_object()
        data = super().retrieve(request, *args, **kwargs).data
        return Response({**data, **moderation_details(request.user, comment, comment=comment)})


class ModerationTargetViewSet(BaseViewSet):
    permission_classes = [IsModerator, CanModerateAuthor]
    lookup_field = "uuid"
    field = None
    model = None

    def get_queryset(self):
        return self.model.objects.filter(reports__isnull=False).distinct()

    def warn(self, request, uuid):
        target = self.get_object()
        if Warning.objects.filter(**{self.field: target}).exists():
            return Response(
                {"detail": "Dieser Inhalt wurde bereits verwarnt."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = WarningModelSerializer.write(data=request.data)
        serializer.is_valid(raise_exception=True)
        warning = issue_warning(
            target, self.field, request.user, serializer.validated_data["reason"]
        )
        return Response(
            {"warning": WarningModelSerializer.read(warning).data, "report_count": 0},
            status=status.HTTP_201_CREATED,
        )

    def dismiss(self, request, uuid):
        self.get_object().reports.resolve()
        return Response({"report_count": 0})


class PostModerationViewSet(ModerationTargetViewSet):
    field = "post"
    model = Post


class CommentModerationViewSet(ModerationTargetViewSet):
    field = "comment"
    model = Comment


class StatusViewSet(BaseViewSet, mixins.RetrieveModelMixin):
    permission_classes = [IsAuthenticated, CanViewWarnings]
    lookup_field = "username"

    def get_queryset(self):
        return User.objects.filter(is_active=True)

    def retrieve(self, request, *args, **kwargs):
        return Response(status_of(self.get_object(), request.user))
