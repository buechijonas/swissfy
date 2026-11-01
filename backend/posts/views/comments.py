from django.shortcuts import get_object_or_404
from rest_framework import mixins
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from commons.views import BaseViewSet, CreateModelMixin
from main.numbers import compact_number
from notifications.models import Notification
from notifications.notify import notify

from ..models import Comment, CommentVote, Post
from ..permissions import IsAuthor, IsNotSuspended
from ..serializers import CommentModelSerializer, PostModelSerializer
from .pagination import OldestFirst


def notify_comment(comment):
    notify(
        comment.post.author,
        Notification.Kind.COMMENT,
        actor=comment.author,
        post=comment.post,
        comment=comment,
    )


def post_summary(post, visible, context):
    if post.pk in visible:
        return PostModelSerializer.summary(visible[post.pk], context=context).data
    return post.unavailable


class PostCommentViewSet(BaseViewSet, mixins.ListModelMixin, CreateModelMixin):
    serializer_class = CommentModelSerializer
    pagination_class = OldestFirst
    permission_action_classes = {"create": [IsAuthenticated, IsNotSuspended]}

    def comments(self):
        return Comment.objects.visible_to(self.request.user)

    def get_post(self):
        return get_object_or_404(
            Post.objects.apply_acl(self.request.user), uuid=self.kwargs["uuid"]
        )

    def get_queryset(self):
        comments = self.comments().filter(post=self.get_post(), parent=None)
        return comments.with_details(self.request.user)

    def list(self, request, *args, **kwargs):
        page = Comment.attach_latest_replies(
            self.paginate_queryset(self.get_queryset()),
            self.comments().with_details(request.user),
        )
        serializer = CommentModelSerializer.read(
            page, many=True, context=self.get_serializer_context()
        )
        return self.get_paginated_response(serializer.data)

    def perform_create(self, serializer):
        comment = serializer.save(post=self.get_post(), author=self.request.user)
        notify_comment(comment)
        return comment


class CommentReplyViewSet(PostCommentViewSet):
    def get_parent(self):
        comments = Comment.objects.apply_acl(self.request.user).with_details(self.request.user)
        return get_object_or_404(comments, uuid=self.kwargs["uuid"])

    def get_queryset(self):
        replies = self.comments().filter(parent=self.get_parent())
        return replies.with_details(self.request.user)

    def perform_create(self, serializer):
        parent = self.get_parent()
        if not Post.objects.apply_acl(self.request.user).filter(pk=parent.post_id).exists():
            raise PermissionDenied("Dieser Feed ist nicht mehr verfügbar.")
        comment = serializer.save(post=parent.post, parent=parent, author=self.request.user)
        notify_comment(comment)
        return comment


class CommentViewSet(BaseViewSet, mixins.RetrieveModelMixin, mixins.DestroyModelMixin):
    serializer_class = CommentModelSerializer
    lookup_field = "uuid"
    permission_action_classes = {"destroy": [IsAuthenticated, IsAuthor]}

    def get_queryset(self):
        return Comment.objects.apply_acl(self.request.user).with_details(self.request.user)

    def get_posts(self):
        return Post.objects.apply_acl(self.request.user).with_details(self.request.user)

    def retrieve(self, request, *args, **kwargs):
        comment = self.get_object()
        ids = comment.ancestor_ids
        visible = self.get_queryset().in_bulk(ids)
        ancestors = Comment.objects.select_related("author").in_bulk(ids)
        posts = self.get_posts().in_bulk([comment.post_id])
        return Response(
            {
                **self.get_serializer(comment).data,
                "ancestors": [
                    (
                        self.get_serializer(visible[pk]).data
                        if pk in visible
                        else ancestors[pk].unavailable
                    )
                    for pk in ids
                ],
                "post": post_summary(comment.post, posts, self.get_serializer_context()),
            }
        )

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.delete()
        comments = Comment.objects.visible_to(request.user)
        parent = self.get_queryset().filter(pk=comment.parent_id).first()
        if parent:
            Comment.attach_latest_replies([parent], comments.with_details(request.user))
        context = self.get_serializer_context()
        return Response(
            {
                "parent": (
                    CommentModelSerializer.read(parent, context=context).data if parent else None
                ),
                "comment_count": comments.filter(post=comment.post_id, parent=None).count(),
            }
        )

    def vote(self, request, uuid):
        comment = self.get_object()
        if comment.author_id == request.user.pk:
            raise PermissionDenied("Du kannst nicht über eigene Kommentare abstimmen.")
        serializer = CommentModelSerializer.vote(data=request.data)
        serializer.is_valid(raise_exception=True)
        value = serializer.validated_data["value"]

        votes = CommentVote.objects.filter(user=request.user, comment=comment)
        if value:
            votes.update_or_create(user=request.user, comment=comment, defaults={"value": value})
        else:
            votes.delete()
        comment = self.get_queryset().get(pk=comment.pk)
        return Response({"score": compact_number(comment.score), "my_vote": comment.my_vote})
