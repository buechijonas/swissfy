from datetime import timedelta
from urllib.parse import urlencode
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import OuterRef, Q, Subquery
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.roles import is_moderator
from main.parsers import JSONParser
from moderation.sanctions import ensure_not_suspended
from social.serializers import can_view_profile

from ..models import Comment, Post, PostCreation, SavedPost
from ..queries import (
    comment_details,
    comment_visibility,
    feed,
    image_posts,
    media_posts,
    reported_comments,
    video_posts,
    visible_posts,
    with_details,
)
from ..serializers import CommentSerializer, PostCreateSerializer, PostSerializer
from .comments import post_summary
from .pagination import FeedOrder, NewestFirst, SavedOrder
from .posts import check_quota

User = get_user_model()


def starting_from(posts, request):
    try:
        start = UUID(request.query_params.get("from", ""))
    except ValueError:
        return posts
    return posts.filter(pk__lte=Subquery(Post.objects.filter(uuid=start).values("pk")))


def by_media(posts, request):
    if request.query_params.get("images"):
        posts = image_posts(posts)
    if request.query_params.get("videos"):
        posts = video_posts(posts)
    if request.query_params.get("media"):
        posts = media_posts(posts)
    return starting_from(posts, request)


class FeedView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    pagination_class = FeedOrder
    parser_classes = [MultiPartParser, JSONParser]

    def get_queryset(self):
        return with_details(feed(self.request.user), self.request.user)

    def create(self, request, *args, **kwargs):
        ensure_not_suspended(request.user)
        check_quota(request.user)
        serializer = PostCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            User.objects.select_for_update().get(pk=request.user.pk)
            check_quota(request.user)
            PostCreation.objects.filter(
                author=request.user, created_at__lt=timezone.now() - timedelta(days=1)
            ).delete()
            PostCreation.objects.create(author=request.user)
            created = serializer.save()
        post = with_details(visible_posts(request.user), request.user).get(pk=created.pk)
        return Response(
            PostSerializer(post, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class UserPostListView(generics.ListAPIView):
    serializer_class = PostSerializer
    pagination_class = NewestFirst

    def get_queryset(self):
        posts = visible_posts(self.request.user).filter(author__username=self.kwargs["username"])
        return with_details(by_media(posts, self.request), self.request.user)


class ReelFeedView(generics.ListAPIView):
    serializer_class = PostSerializer
    pagination_class = NewestFirst

    def get_queryset(self):
        reels = feed(self.request.user).filter(video_status=Post.VideoStatus.READY)
        return with_details(starting_from(reels, self.request), self.request.user)


class ActivityView(APIView):
    def get(self, request, username):
        viewer = request.user
        posts = visible_posts(viewer).filter(author__username=username)
        on_visible_post = Q(post__in=visible_posts(viewer).values("pk")) | Q(author=viewer)
        if is_moderator(viewer):
            on_visible_post |= reported_comments()
        comments = Comment.objects.filter(
            comment_visibility(viewer), on_visible_post, author__username=username
        )
        author = User.objects.filter(username=username).select_related("profile").first()
        if author and not can_view_profile(viewer, author):
            comments = (
                comments.filter(reported_comments()) if is_moderator(viewer) else comments.none()
            )
        comments = comment_details(comments, viewer)
        if request.query_params.get("comments"):
            posts = posts.none()
        else:
            comments = comments.none()
        before = parse_datetime(request.query_params.get("before", ""))
        if before:
            posts = posts.filter(created_at__lt=before)
            comments = comments.filter(created_at__lt=before)

        page_size = NewestFirst.page_size
        posts = list(with_details(posts, viewer).order_by("-created_at")[:page_size])
        comments = list(comments.order_by("-created_at")[:page_size])
        context_posts = Post.objects.all() if is_moderator(viewer) else visible_posts(viewer)
        post_ids = {comment.post_id for comment in comments}
        visible = with_details(context_posts, viewer).in_bulk(post_ids)
        commented = Post.objects.select_related("author").in_bulk(post_ids)
        items = sorted(posts + comments, key=lambda item: item.created_at, reverse=True)
        items = items[:page_size]

        context = {"request": request}
        results = [
            (
                {
                    "type": "comment",
                    **CommentSerializer(item, context=context).data,
                    "post": post_summary(commented[item.post_id], visible, context),
                }
                if isinstance(item, Comment)
                else {"type": "post", **PostSerializer(item, context=context).data}
            )
            for item in items
        ]
        next_page = None
        if len(items) == page_size:
            next_page = f"?{urlencode({'before': items[-1].created_at.isoformat()})}"
        return Response({"results": results, "next": next_page})


class SavedListView(generics.ListAPIView):
    serializer_class = PostSerializer
    pagination_class = SavedOrder

    def get_queryset(self):
        saves = SavedPost.objects.filter(user=self.request.user)
        folder = self.request.query_params.get("folder")
        if folder == "none":
            saves = saves.filter(folder=None)
        elif folder and folder.isdigit():
            saves = saves.filter(folder=folder)
        elif folder:
            saves = saves.none()
        posts = (
            visible_posts(self.request.user)
            .filter(pk__in=saves.values("post"))
            .annotate(saved_at=Subquery(saves.filter(post=OuterRef("pk")).values("created_at")))
        )
        return with_details(posts, self.request.user)
