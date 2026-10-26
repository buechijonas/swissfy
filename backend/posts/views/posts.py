from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, Throttled
from rest_framework.response import Response
from rest_framework.views import APIView

from main.numbers import compact_number
from notifications.models import Notification
from notifications.notify import notify, withdraw

from ..models import Like, Post, PostCreation, Repost, SavedFolder, SavedPost
from ..queries import visible_posts, with_details
from ..serializers import PostAudienceSerializer, PostSerializer

POSTS_PER_DAY = 10


def visible_post(request, uuid):
    return get_object_or_404(visible_posts(request.user), uuid=uuid)


def remaining_posts(user):
    creations = PostCreation.objects.filter(author=user)
    recent = creations.filter(created_at__gte=timezone.now() - timedelta(days=1))
    return max(0, POSTS_PER_DAY - recent.count())


def check_quota(user):
    if not remaining_posts(user):
        raise Throttled(detail=f"Du kannst höchstens {POSTS_PER_DAY} Feeds pro Tag erstellen.")


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer
    lookup_field = "uuid"
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return with_details(visible_posts(self.request.user), self.request.user)

    def update(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author_id != request.user.pk:
            raise PermissionDenied("Du kannst nur eigene Feeds bearbeiten.")
        serializer = PostAudienceSerializer(post, data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(self.get_serializer(self.get_object()).data)

    def perform_destroy(self, post):
        if post.author_id != self.request.user.pk:
            raise PermissionDenied("Du kannst nur eigene Feeds löschen.")
        post.delete()


class PostQuotaView(APIView):
    def get(self, request):
        return Response({"limit": POSTS_PER_DAY, "remaining": remaining_posts(request.user)})


class LikeView(APIView):
    def post(self, request, uuid):
        post = visible_post(request, uuid)
        _, created = Like.objects.get_or_create(user=request.user, post=post)
        if created:
            notify(post.author, Notification.Kind.LIKE, actor=request.user, post=post)
        return self.state(post, True)

    def delete(self, request, uuid):
        post = visible_post(request, uuid)
        Like.objects.filter(user=request.user, post=post).delete()
        withdraw(post.author, Notification.Kind.LIKE, request.user, post=post)
        return self.state(post, False)

    def state(self, post, liked):
        return Response({"liked": liked, "like_count": compact_number(post.likes.count())})


class RepostView(APIView):
    def post(self, request, uuid):
        post = visible_post(request, uuid)
        if post.author == request.user:
            return Response(
                {"detail": "Du kannst deine eigenen Feeds nicht reposten."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        Repost.objects.get_or_create(user=request.user, post=post)
        return self.state(request, post)

    def delete(self, request, uuid):
        post = visible_post(request, uuid)
        Repost.objects.filter(user=request.user, post=post).delete()
        return self.state(request, post)

    def state(self, request, post):
        post = with_details(Post.objects.filter(pk=post.pk), request.user).get()
        return Response({"reposted": post.reposted, "reposter": post.reposter})


class SaveView(APIView):
    def put(self, request, uuid):
        folder = request.data.get("folder")
        if folder is not None:
            folder = get_object_or_404(SavedFolder, pk=folder, owner=request.user)
        SavedPost.objects.update_or_create(
            user=request.user, post=visible_post(request, uuid), defaults={"folder": folder}
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, uuid):
        SavedPost.objects.filter(user=request.user, post=visible_post(request, uuid)).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
