from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.dateparse import parse_datetime
from rest_framework import mixins
from rest_framework.response import Response

from commons.views import BaseViewSet
from swissfy.accounts.roles import is_moderator
from swissfy.social.serializers import can_view_profile

from ..models import Comment, Post, reported_comments
from ..serializers import CommentModelSerializer, PostModelSerializer
from .comments import post_summary
from .pagination import NewestFirst
from .posts import starting_from

User = get_user_model()


class UserPostViewSet(BaseViewSet, mixins.ListModelMixin):
    serializer_class = PostModelSerializer
    pagination_class = NewestFirst

    def get_queryset(self):
        user = self.request.user
        posts = Post.objects.apply_acl(user).filter(author__username=self.kwargs["username"])
        posts = starting_from(posts.by_media(self.request.query_params), self.request.query_params)
        return posts.with_details(user)

    def comments(self, username):
        viewer = self.request.user
        on_visible_post = Q(post__in=Post.objects.apply_acl(viewer).values("pk")) | Q(author=viewer)
        if is_moderator(viewer):
            on_visible_post |= reported_comments()
        comments = Comment.objects.visible_to(viewer).filter(
            on_visible_post, author__username=username
        )
        author = User.objects.filter(username=username).select_related("profile").first()
        if author and not can_view_profile(viewer, author):
            if is_moderator(viewer):
                comments = comments.filter(reported_comments())
            else:
                comments = comments.none()
        return comments.with_details(viewer)

    def activities(self, request, username):
        viewer = request.user
        posts = Post.objects.apply_acl(viewer).filter(author__username=username)
        comments = self.comments(username)
        if request.query_params.get("comments"):
            posts = posts.none()
        else:
            comments = comments.none()
        before = parse_datetime(request.query_params.get("before", ""))
        if before:
            posts = posts.filter(created_at__lt=before)
            comments = comments.filter(created_at__lt=before)

        page_size = NewestFirst.page_size
        posts = list(posts.with_details(viewer).order_by("-created_at")[:page_size])
        comments = list(comments.order_by("-created_at")[:page_size])
        context_posts = (
            Post.objects.all() if is_moderator(viewer) else Post.objects.apply_acl(viewer)
        )
        post_ids = {comment.post_id for comment in comments}
        visible = context_posts.with_details(viewer).in_bulk(post_ids)
        commented = Post.objects.select_related("author").in_bulk(post_ids)

        context = self.get_serializer_context()
        items = [(post.created_at, self.post_item(post, context)) for post in posts] + [
            (comment.created_at, self.comment_item(comment, commented, visible, context))
            for comment in comments
        ]
        items = sorted(items, key=lambda item: item[0], reverse=True)[:page_size]
        next_page = None
        if len(items) == page_size:
            next_page = f"?{urlencode({'before': items[-1][0].isoformat()})}"
        return Response({"results": [data for _, data in items], "next": next_page})

    def post_item(self, post, context):
        return {"type": "post", **PostModelSerializer.read(post, context=context).data}

    def comment_item(self, comment, commented, visible, context):
        return {
            "type": "comment",
            **CommentModelSerializer.read(comment, context=context).data,
            "post": post_summary(commented[comment.post_id], visible, context),
        }
