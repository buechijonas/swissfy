from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from commons.exceptions import BadRequest
from commons.views import BaseViewSet, CreateModelMixin
from main.parsers import JSONParser
from swissfy.notifications.models import Notification

from ..models import (
    POSTS_PER_DAY,
    Like,
    Post,
    PostCreation,
    Repost,
    SavedFolder,
    SavedPost,
)
from ..permissions import HasPostQuota, IsAuthor, IsNotSuspended
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
    mixins.DestroyModelMixin,
):
    serializer_class = PostModelSerializer
    parser_classes = [MultiPartParser, JSONParser]
    lookup_field = "uuid"
    lookup_value_converter = "uuid"
    pagination_class = NewestFirst
    pagination_action_classes = {"list": FeedOrder, "saved": SavedOrder}
    permission_action_classes = {
        "create": [IsAuthenticated, IsNotSuspended, HasPostQuota],
        "audience": [IsAuthenticated, IsAuthor],
        "destroy": [IsAuthenticated, IsAuthor],
    }

    def get_queryset(self):
        user = self.request.user
        posts = Post.objects.feed(user) if self.action == "list" else Post.objects.apply_acl(user)
        return posts.with_details(user)

    def get_serializer_class(self):
        if self.action == "audience":
            return PostModelSerializer.audience
        return super().get_serializer_class()

    def perform_create(self, serializer):
        with transaction.atomic():
            User.objects.select_for_update().get(pk=self.request.user.pk)
            self.check_permissions(self.request)
            PostCreation.objects.filter(author=self.request.user).stale().delete()
            PostCreation.objects.create(author=self.request.user)
            return serializer.save()

    @action(detail=True, methods=["put"])
    def audience(self, request, uuid):
        serializer = self.get_serializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.respond(serializer.save())

    @action(detail=False)
    def quota(self, request):
        remaining = PostCreation.objects.remaining(request.user)
        return Response({"limit": POSTS_PER_DAY, "remaining": remaining})

    @action(detail=False, url_path="global", permission_classes=[AllowAny])
    def global_feed(self, request):
        posts = Post.objects.apply_acl(request.user).filter(visibility=Post.Visibility.GLOBAL)
        return self.paginated(posts)

    @action(detail=False)
    def reels(self, request):
        reels = Post.objects.feed(request.user).videos()
        return self.paginated(starting_from(reels, request.query_params))

    @action(detail=False)
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

    @action(detail=True, methods=["post"])
    def like(self, request, uuid):
        post = self.get_object()
        _, created = Like.objects.get_or_create(user=request.user, post=post)
        if created:
            Notification.notify(post.author, Notification.Kind.LIKE, actor=request.user, post=post)
        return self.respond(post)

    @like.mapping.delete
    def unlike(self, request, uuid):
        post = self.get_object()
        Like.objects.filter(user=request.user, post=post).delete()
        Notification.objects.withdraw(post.author, Notification.Kind.LIKE, request.user, post=post)
        return self.respond(post)

    @action(detail=True, methods=["post"])
    def repost(self, request, uuid):
        post = self.get_object()
        if post.is_own:
            raise BadRequest("Du kannst deine eigenen Feeds nicht reposten.")
        Repost.objects.get_or_create(user=request.user, post=post)
        return self.respond(post)

    @repost.mapping.delete
    def unrepost(self, request, uuid):
        post = self.get_object()
        Repost.objects.filter(user=request.user, post=post).delete()
        return self.respond(post)

    @action(detail=True, methods=["put"])
    def save(self, request, uuid):
        folder = request.data.get("folder")
        if folder is not None:
            folder = get_object_or_404(SavedFolder, pk=folder, owner=request.user)
        post = self.get_object()
        SavedPost.objects.update_or_create(
            user=request.user, post=post, defaults={"folder": folder}
        )
        return self.respond(post)

    @save.mapping.delete
    def unsave(self, request, uuid):
        post = self.get_object()
        SavedPost.objects.filter(user=request.user, post=post).delete()
        return self.respond(post)
