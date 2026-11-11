from django.shortcuts import get_object_or_404
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from commons.views import BaseViewSet

from .. import hashtags
from ..models import Hashtag, Post
from ..serializers import HashtagModelSerializer, PostModelSerializer
from .pagination import NewestFirst
from .posts import starting_from


class HashtagViewSet(BaseViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    lookup_field = "name"
    serializer_class = HashtagModelSerializer
    pagination_class = None

    def get_queryset(self):
        return Hashtag.objects.with_stats(self.request.user)

    def list(self, request, *args, **kwargs):
        query = hashtags.normalize(request.query_params.get("q", ""))
        tags = Hashtag.objects.none()
        if query:
            tags = self.get_queryset().filter(name__startswith=query, post_count__gt=0)
            tags = tags.order_by("-post_count", "name")[:20]
        return Response(self.get_serializer(tags, many=True).data)

    def get_object(self):
        name = hashtags.normalize(self.kwargs["name"])
        return get_object_or_404(self.get_queryset(), name=name)

    @action(detail=True, methods=["put"])
    def follow(self, request, name):
        self.get_object().followers.add(request.user)
        return self.retrieve(request)

    @follow.mapping.delete
    def unfollow(self, request, name):
        self.get_object().followers.remove(request.user)
        return self.retrieve(request)

    def retrieve(self, request, *args, **kwargs):
        serializer = HashtagModelSerializer.read(
            self.get_object(), context=self.get_serializer_context()
        )
        return Response(serializer.data)


class HashtagPostViewSet(BaseViewSet, mixins.ListModelMixin):
    serializer_class = PostModelSerializer
    pagination_class = NewestFirst

    def get_queryset(self):
        user = self.request.user
        name = hashtags.normalize(self.kwargs["name"])
        posts = Post.objects.apply_acl(user).filter(hashtags__name=name)
        posts = starting_from(posts.by_media(self.request.query_params), self.request.query_params)
        return posts.with_details(user)
