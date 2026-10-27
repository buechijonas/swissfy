from django.db.models import Count, Exists, OuterRef, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics

from .. import hashtags
from ..models import Hashtag
from ..queries import visible_posts, with_details
from ..serializers import HashtagSerializer, PostSerializer
from .feeds import by_media
from .pagination import NewestFirst


def hashtags_for(viewer):
    followers = Hashtag.followers.through.objects.filter(hashtag=OuterRef("pk"), user=viewer)
    visible = visible_posts(viewer).values("pk")
    return Hashtag.objects.annotate(
        post_count=Count("posts", filter=Q(posts__in=visible), distinct=True),
        following=Exists(followers),
    )


class HashtagSearchView(generics.ListAPIView):
    serializer_class = HashtagSerializer
    pagination_class = None

    def get_queryset(self):
        query = hashtags.normalize(self.request.query_params.get("q", ""))
        if not query:
            return Hashtag.objects.none()
        tags = hashtags_for(self.request.user).filter(name__startswith=query, post_count__gt=0)
        return tags.order_by("-post_count", "name")[:20]


class HashtagDetailView(generics.RetrieveAPIView):
    serializer_class = HashtagSerializer

    def get_object(self):
        name = hashtags.normalize(self.kwargs["name"])
        return get_object_or_404(hashtags_for(self.request.user), name=name)


class HashtagFollowView(HashtagDetailView):
    def put(self, request, name):
        self.get_object().followers.add(request.user)
        return self.retrieve(request)

    def delete(self, request, name):
        self.get_object().followers.remove(request.user)
        return self.retrieve(request)


class HashtagPostListView(generics.ListAPIView):
    serializer_class = PostSerializer
    pagination_class = NewestFirst

    def get_queryset(self):
        name = hashtags.normalize(self.kwargs["name"])
        posts = visible_posts(self.request.user).filter(hashtags__name=name)
        return with_details(by_media(posts, self.request), self.request.user)
