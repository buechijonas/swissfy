from django.contrib.auth import get_user_model
from django.db.models import Count, Max, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.roles import IsModerator, Role, is_admin, is_moderator, outranks
from main.pagination import NextPagePagination
from notifications.models import Notification
from notifications.notify import notify
from posts.models import Comment, Post
from posts.queries import comment_details, with_details
from posts.serializers import CommentSerializer, PostSerializer, PostSummarySerializer
from posts.views import (
    CommentDetailView,
    CommentListView,
    CommentReplyListView,
    visible_comments,
    visible_post,
)

from .models import Reason, Report, Suspension, Warning
from .sanctions import suspend_if_needed
from .serializers import SuspensionSerializer, WarningSerializer, reason_options

User = get_user_model()


class ReportView(APIView):
    def target(self, request, uuid):
        raise NotImplementedError

    def post(self, request, uuid):
        target = self.target(request, uuid)
        if target.author_id == request.user.pk:
            raise PermissionDenied("Du kannst eigene Inhalte nicht melden.")
        if is_moderator(request.user) and outranks(target.author, request.user):
            raise PermissionDenied("Inhalte von Admins kannst du nicht melden.")
        Report.objects.get_or_create(reporter=request.user, **{self.field: target})
        return Response({"reported": True})


class PostReportView(ReportView):
    field = "post"

    def target(self, request, uuid):
        return visible_post(request, uuid)


class CommentReportView(ReportView):
    field = "comment"

    def target(self, request, uuid):
        return get_object_or_404(visible_comments(request.user), uuid=uuid)


def moderation_context(request):
    return {"request": request, "moderation": True}


class ReportQueueView(APIView):
    permission_classes = [IsModerator]

    def get(self, request):
        open_reports = Report.objects.filter(resolved_at=None)
        if request.query_params.get("status") == "resolved":
            reports = (
                Report.objects.filter(resolved_at__isnull=False)
                .exclude(post__in=open_reports.values("post"))
                .exclude(comment__in=open_reports.values("comment"))
            )
            last_activity = Max("resolved_at")
        else:
            reports = open_reports
            last_activity = Max("created_at")
        if not is_admin(request.user):
            reports = reports.exclude(
                Q(post__author__groups__name=Role.ADMIN.label)
                | Q(comment__author__groups__name=Role.ADMIN.label)
            )
        groups = (
            reports.values("post", "comment")
            .annotate(report_count=Count("id"), last_activity=last_activity)
            .order_by("-last_activity")
        )
        paginator = NextPagePagination()
        page = paginator.paginate_queryset(groups, request, view=self)

        viewer = request.user
        context = moderation_context(request)
        posts = with_details(
            Post.objects.filter(pk__in=[item["post"] for item in page if item["post"]]), viewer
        ).in_bulk()
        comments = comment_details(
            Comment.objects.filter(pk__in=[item["comment"] for item in page if item["comment"]]),
            viewer,
        ).in_bulk()
        summaries = with_details(
            Post.objects.filter(pk__in=[comment.post_id for comment in comments.values()]), viewer
        ).in_bulk()

        warnings = Warning.objects.filter(Q(post__in=posts) | Q(comment__in=comments))
        warned = {(warning.post_id, warning.comment_id) for warning in warnings}

        results = []
        for item in page:
            summary = {
                "report_count": item["report_count"],
                "warned": (item["post"], item["comment"]) in warned,
            }
            if item["post"]:
                post = PostSerializer(posts[item["post"]], context=context).data
                results.append({"type": "post", **summary, "post": post})
            else:
                comment = comments[item["comment"]]
                results.append(
                    {
                        "type": "comment",
                        **summary,
                        "comment": CommentSerializer(comment, context=context).data,
                        "post": PostSummarySerializer(
                            summaries[comment.post_id], context=context
                        ).data,
                    }
                )
        return paginator.get_paginated_response(results)


def open_reports(**target):
    return Report.objects.filter(resolved_at=None, **target)


def moderation_details(viewer, **target):
    item = next(iter(target.values()))
    return {
        "report_count": open_reports(**target).count(),
        "can_warn": not Warning.objects.filter(**target).exists()
        and not outranks(item.author, viewer),
        "reasons": reason_options(),
        "warnings": WarningSerializer(Warning.objects.filter(**target), many=True).data,
    }


def moderated_posts():
    reported = Q(reports__isnull=False) | Q(comments__reports__isnull=False)
    return Post.objects.filter(pk__in=Post.objects.filter(reported).values("pk"))


def reported_post(request, uuid):
    return get_object_or_404(with_details(moderated_posts(), request.user), uuid=uuid)


class ModerationPostView(APIView):
    permission_classes = [IsModerator]

    def get(self, request, uuid):
        post = reported_post(request, uuid)
        return Response(
            {
                "post": PostSerializer(post, context=moderation_context(request)).data,
                **moderation_details(request.user, post=post),
            }
        )


class ModerationPostCommentsView(CommentListView):
    permission_classes = [IsModerator]
    http_method_names = ["get"]

    def comment_visibility(self):
        return Q()

    def get_post(self):
        return reported_post(self.request, self.kwargs["uuid"])

    def get_serializer_context(self):
        return moderation_context(self.request)


def moderated_comments(viewer):
    return comment_details(Comment.objects.filter(post__in=moderated_posts()), viewer)


class ModerationCommentRepliesView(CommentReplyListView):
    permission_classes = [IsModerator]
    http_method_names = ["get"]

    def comment_visibility(self):
        return Q()

    def parent(self):
        return get_object_or_404(moderated_comments(self.request.user), uuid=self.kwargs["uuid"])

    def get_serializer_context(self):
        return moderation_context(self.request)


class ModerationCommentView(CommentDetailView):
    permission_classes = [IsModerator]
    http_method_names = ["get"]

    def get_queryset(self):
        return moderated_comments(self.request.user)

    def get_posts(self):
        return with_details(moderated_posts(), self.request.user)

    def get_object(self):
        return get_object_or_404(self.get_queryset(), uuid=self.kwargs["uuid"])

    def get_serializer_context(self):
        return moderation_context(self.request)

    def retrieve(self, request, *args, **kwargs):
        data = super().retrieve(request, *args, **kwargs).data
        return Response({**data, **moderation_details(request.user, comment=self.get_object())})


class ResolveView(APIView):
    permission_classes = [IsModerator]

    def target(self, uuid):
        model = Post if self.field == "post" else Comment
        target = get_object_or_404(model.objects.distinct(), uuid=uuid, reports__isnull=False)
        if outranks(target.author, self.request.user):
            raise PermissionDenied("Inhalte von Admins können nur Admins bearbeiten.")
        return target

    def resolve(self, target):
        open_reports(**{self.field: target}).update(resolved_at=timezone.now())


class WarnView(ResolveView):
    def post(self, request, uuid):
        target = self.target(uuid)
        if Warning.objects.filter(**{self.field: target}).exists():
            return Response(
                {"detail": "Dieser Inhalt wurde bereits verwarnt."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reason = request.data.get("reason")
        if reason not in Reason.values:
            return Response({"reason": ["Wähle einen Grund."]}, status=status.HTTP_400_BAD_REQUEST)
        warning = Warning.objects.create(
            user_id=target.author_id, moderator=request.user, reason=reason, **{self.field: target}
        )
        self.resolve(target)
        self.hide(target)
        notify(warning.user, Notification.Kind.WARNING, warning=warning)
        suspend_if_needed(warning)
        return Response(
            {"warning": WarningSerializer(warning).data, "report_count": 0},
            status=status.HTTP_201_CREATED,
        )

    def hide(self, target):
        now = timezone.now()
        if self.field == "post":
            Post.objects.filter(pk=target.pk).update(hidden_at=now)
            return
        ids = [target.pk]
        while ids:
            Comment.objects.filter(pk__in=ids).update(hidden_at=now)
            ids = list(
                Comment.objects.filter(parent__in=ids, hidden_at=None).values_list("pk", flat=True)
            )


class DismissView(ResolveView):
    def post(self, request, uuid):
        self.resolve(self.target(uuid))
        return Response({"report_count": 0})


class PostWarnView(WarnView):
    field = "post"


class CommentWarnView(WarnView):
    field = "comment"


class PostDismissView(DismissView):
    field = "post"


class CommentDismissView(DismissView):
    field = "comment"


def reported_content(user):
    groups = (
        Report.objects.filter(Q(post__author=user) | Q(comment__author=user))
        .values("post", "post__uuid", "post__text", "comment", "comment__uuid", "comment__text")
        .annotate(
            report_count=Count("id"),
            open_count=Count("id", filter=Q(resolved_at=None)),
            last_reported_at=Max("created_at"),
        )
        .order_by("-last_reported_at")
    )
    return [
        {
            "type": "Feed" if group["post"] else "Kommentar",
            "text": group["post__text"] if group["post"] else group["comment__text"],
            "report_count": group["report_count"],
            "open_count": group["open_count"],
            "link": (
                f"/moderation/posts/{group['post__uuid']}"
                if group["post"]
                else f"/moderation/comments/{group['comment__uuid']}"
            ),
        }
        for group in groups
    ]


def can_view_warnings(viewer, user):
    return user == viewer or is_moderator(viewer)


class StatusView(APIView):
    def get(self, request, username):
        user = get_object_or_404(User, username=username, is_active=True)
        if not can_view_warnings(request.user, user):
            raise PermissionDenied("Du kannst diese Verwarnungen nicht sehen.")
        context = {"moderation": is_moderator(request.user)}
        warnings = Warning.objects.filter(user=user).select_related("post", "comment")
        suspensions = Suspension.objects.filter(user=user).select_related("warning")
        events = [
            *WarningSerializer(warnings, many=True, context=context).data,
            *SuspensionSerializer(suspensions, many=True).data,
        ]
        events.sort(
            key=lambda event: (event["caused_at"], event["type"] == "suspension"), reverse=True
        )
        reports = reported_content(user) if is_moderator(request.user) else None
        return Response({"events": events, "reports": reports})
