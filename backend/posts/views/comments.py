from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from main.numbers import compact_number
from moderation.sanctions import ensure_not_suspended
from notifications.models import Notification
from notifications.notify import notify

from ..models import Comment, CommentVote
from ..queries import (
    attach_latest_replies,
    comment_details,
    comment_visibility,
    unavailable,
    visible_posts,
    with_details,
)
from ..serializers import CommentSerializer, PostSummarySerializer
from .pagination import OldestFirst
from .posts import visible_post


def notify_comment(comment):
    notify(
        comment.post.author,
        Notification.Kind.COMMENT,
        actor=comment.author,
        post=comment.post,
        comment=comment,
    )


def visible_comments(viewer):
    on_visible_post = Q(post__in=visible_posts(viewer)) | Q(author=viewer)
    comments = Comment.objects.filter(comment_visibility(viewer), on_visible_post)
    return comment_details(comments, viewer)


def post_summary(post, visible, context):
    if post.pk in visible:
        return PostSummarySerializer(visible[post.pk], context=context).data
    return unavailable(post, "Feed")


class CommentListView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    pagination_class = OldestFirst

    def get_post(self):
        return visible_post(self.request, self.kwargs["uuid"])

    def comment_visibility(self):
        return comment_visibility(self.request.user)

    def get_queryset(self):
        comments = self.get_post().comments.filter(self.comment_visibility(), parent=None)
        return comment_details(comments, self.request.user)

    def list(self, request, *args, **kwargs):
        page = attach_latest_replies(
            self.paginate_queryset(self.get_queryset()),
            request.user,
            self.comment_visibility(),
        )
        return self.get_paginated_response(self.get_serializer(page, many=True).data)

    def create(self, request, *args, **kwargs):
        ensure_not_suspended(request.user)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        comment = serializer.save(
            post=visible_post(self.request, self.kwargs["uuid"]), author=self.request.user
        )
        notify_comment(comment)


class CommentReplyListView(CommentListView):
    def parent(self):
        return get_object_or_404(visible_comments(self.request.user), uuid=self.kwargs["uuid"])

    def get_queryset(self):
        replies = self.parent().replies.filter(self.comment_visibility())
        return comment_details(replies, self.request.user)

    def perform_create(self, serializer):
        parent = self.parent()
        if not visible_posts(self.request.user).filter(pk=parent.post_id).exists():
            raise PermissionDenied("Dieser Feed ist nicht mehr verfügbar.")
        comment = serializer.save(post=parent.post, parent=parent, author=self.request.user)
        notify_comment(comment)


class CommentDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = CommentSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return visible_comments(self.request.user)

    def get_posts(self):
        return with_details(visible_posts(self.request.user), self.request.user)

    def retrieve(self, request, *args, **kwargs):
        comment = self.get_object()
        chain = []
        parent_id = comment.parent_id
        while parent_id:
            chain.append(parent_id)
            parent_id = Comment.objects.values_list("parent_id", flat=True).get(pk=parent_id)
        ancestors = self.get_queryset().in_bulk(chain)
        hidden_ancestors = Comment.objects.select_related("author").in_bulk(chain)
        context = self.get_serializer_context()
        visible = self.get_posts().in_bulk([comment.post_id])
        return Response(
            {
                **self.get_serializer(comment).data,
                "ancestors": [
                    (
                        self.get_serializer(ancestors[pk]).data
                        if pk in ancestors
                        else unavailable(hidden_ancestors[pk], "Kommentar")
                    )
                    for pk in reversed(chain)
                ],
                "post": post_summary(comment.post, visible, context),
            }
        )

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author_id != request.user.pk:
            raise PermissionDenied("Du kannst nur eigene Kommentare löschen.")
        comment.delete()

        parent = self.get_queryset().filter(pk=comment.parent_id).first()
        if parent:
            parent = attach_latest_replies(
                [parent], request.user, comment_visibility(request.user)
            )[0]
            parent = self.get_serializer(parent).data
        comment_count = Comment.objects.filter(
            comment_visibility(request.user), post=comment.post_id, parent=None
        ).count()
        return Response({"parent": parent, "comment_count": comment_count})


class CommentVoteView(APIView):
    def put(self, request, uuid):
        comment = get_object_or_404(visible_comments(request.user), uuid=uuid)
        if comment.author_id == request.user.pk:
            raise PermissionDenied("Du kannst nicht über eigene Kommentare abstimmen.")
        value = request.data.get("value")
        if value not in (*CommentVote.Value.values, 0):
            return Response({"value": ["Ungültige Stimme."]}, status=status.HTTP_400_BAD_REQUEST)

        votes = CommentVote.objects.filter(user=request.user, comment=comment)
        if value:
            votes.update_or_create(user=request.user, comment=comment, defaults={"value": value})
        else:
            votes.delete()
        comment = visible_comments(request.user).get(pk=comment.pk)
        return Response({"score": compact_number(comment.score), "my_vote": comment.my_vote})
