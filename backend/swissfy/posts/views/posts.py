from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status
from rest_framework.exceptions import Throttled
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from commons.views import BaseViewSet, CreateModelMixin, UpdateModelMixin
from main.numbers import compact_number
from main.parsers import JSONParser
from swissfy.notifications.models import Notification
from swissfy.notifications.notify import notify, withdraw

from ..models import (
    POSTS_PER_DAY,
    Like,
    Post,
    PostCreation,
    Repost,
    SavedFolder,
    SavedPost,
)
from ..permissions import IsAuthor, IsNotSuspended
from ..serializers import PostModelSerializer
from .pagination import FeedOrder, NewestFirst, SavedOrder

User = get_user_model()


def starting_from(posts, params):
    try:
        start = UUID(params.get("from", ""))
    except ValueError:
        return posts
    return posts.filter(pk__lte=Subquery(Post.objects.filter(uuid=start).values("pk")))


class PostViewSet(
    BaseViewSet,
    mixins.ListModelMixin,
    CreateModelMixin,
    mixins.RetrieveModelMixin,
    UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    serializer_class = PostModelSerializer
    parser_classes = [MultiPartParser, JSONParser]
    lookup_field = "uuid"
    pagination_class = NewestFirst
    pagination_action_classes = {"list": FeedOrder, "saved": SavedOrder}
    permission_action_classes = {
        "global_feed": [AllowAny],
        "create": [IsAuthenticated, IsNotSuspended],
        "update": [IsAuthenticated, IsAuthor],
        "destroy": [IsAuthenticated, IsAuthor],
    }

    def get_queryset(self):
        user = self.request.user
        posts = Post.objects.feed(user) if self.action == "list" else Post.objects.apply_acl(user)
        return posts.with_details(user)

    def get_serializer_class(self):
        if self.action == "update":
            return PostModelSerializer.audience
        return super().get_serializer_class()

    def check_quota(self):
        if not PostCreation.objects.remaining(self.request.user):
            raise Throttled(detail=f"Du kannst höchstens {POSTS_PER_DAY} Feeds pro Tag erstellen.")

    def perform_create(self, serializer):
        with transaction.atomic():
            User.objects.select_for_update().get(pk=self.request.user.pk)
            self.check_quota()
            PostCreation.objects.filter(author=self.request.user).stale().delete()
            PostCreation.objects.create(author=self.request.user)
            return serializer.save()

    def create(self, request, *args, **kwargs):
        self.check_quota()
        return super().create(request, *args, **kwargs)

    def quota(self, request):
        remaining = PostCreation.objects.remaining(request.user)
        return Response({"limit": POSTS_PER_DAY, "remaining": remaining})

    def global_feed(self, request):
        posts = Post.objects.apply_acl(request.user).filter(visibility=Post.Visibility.GLOBAL)
        return self.paginated(posts)

    def reels(self, request):
        reels = Post.objects.feed(request.user).videos()
        return self.paginated(starting_from(reels, request.query_params))

    def saved(self, request):
        folder = request.query_params.get("folder")
        saves = SavedPost.objects.filter(user=request.user).in_folder(folder)
        posts = (
            Post.objects.apply_acl(request.user)
            .filter(pk__in=saves.values("post"))
            .annotate(saved_at=Subquery(saves.filter(post=OuterRef("pk")).values("created_at")))
        )
        return self.paginated(posts)

    def paginated(self, posts):
        page = self.paginate_queryset(posts.with_details(self.request.user))
        serializer = PostModelSerializer.read(
            page, many=True, context=self.get_serializer_context()
        )
        return self.get_paginated_response(serializer.data)

    def like(self, request, uuid):
        post = self.get_object()
        _, created = Like.objects.get_or_create(user=request.user, post=post)
        if created:
            notify(post.author, Notification.Kind.LIKE, actor=request.user, post=post)
        return self.like_state(post, True)

    def unlike(self, request, uuid):
        post = self.get_object()
        Like.objects.filter(user=request.user, post=post).delete()
        withdraw(post.author, Notification.Kind.LIKE, request.user, post=post)
        return self.like_state(post, False)

    def like_state(self, post, liked):
        return Response({"liked": liked, "like_count": compact_number(post.likes.count())})

    def repost(self, request, uuid):
        post = self.get_object()
        if post.author == request.user:
            return Response(
                {"detail": "Du kannst deine eigenen Feeds nicht reposten."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        Repost.objects.get_or_create(user=request.user, post=post)
        return self.repost_state()

    def unrepost(self, request, uuid):
        post = self.get_object()
        Repost.objects.filter(user=request.user, post=post).delete()
        return self.repost_state()

    def repost_state(self):
        post = self.get_object()
        return Response({"reposted": post.reposted, "reposter": post.reposter})

    def save(self, request, uuid):
        folder = request.data.get("folder")
        if folder is not None:
            folder = get_object_or_404(SavedFolder, pk=folder, owner=request.user)
        SavedPost.objects.update_or_create(
            user=request.user, post=self.get_object(), defaults={"folder": folder}
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def unsave(self, request, uuid):
        SavedPost.objects.filter(user=request.user, post=self.get_object()).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
