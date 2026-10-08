from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import get_or_create_profile

from .models import Follow, FollowRequest, FriendRequest, Friendship
from .serializers import (
    PrivacySerializer,
    ProfileListSerializer,
    ProfileSerializer,
    are_friends,
    follows,
    requires_follow_request,
)

User = get_user_model()


class ProfilePagination(PageNumberPagination):
    page_size = 20


class ProfileListView(generics.ListAPIView):
    """All other active users, a page at a time."""

    serializer_class = ProfileListSerializer
    pagination_class = ProfilePagination

    def get_queryset(self):
        viewer = self.request.user
        users = User.objects.filter(is_active=True).exclude(pk=viewer.pk)
        return with_viewer_relations(users, viewer).order_by("username")


def with_viewer_relations(users, viewer):
    return users.select_related("profile").annotate(
        viewer_follows=Exists(Follow.objects.filter(follower=viewer, following=OuterRef("pk"))),
        viewer_is_friend=Exists(Friendship.objects.filter(user=viewer, friend=OuterRef("pk"))),
    )


class FollowRequestListView(generics.ListAPIView):
    serializer_class = ProfileListSerializer
    pagination_class = None

    def get_queryset(self):
        viewer = self.request.user
        users = User.objects.filter(
            is_active=True, sent_follow_requests__following=viewer
        ).order_by("sent_follow_requests__created_at")
        return with_viewer_relations(users, viewer)


class FollowRequestView(APIView):
    def get_request(self, request, username):
        return get_object_or_404(
            FollowRequest, follower__username=username, following=request.user
        )

    def post(self, request, username):
        self.get_request(request, username).accept()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, username):
        self.get_request(request, username).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PrivacyView(APIView):
    def get(self, request):
        return Response(PrivacySerializer(get_or_create_profile(request.user)).data)

    def patch(self, request):
        serializer = PrivacySerializer(
            get_or_create_profile(request.user), data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if not requires_follow_request(request.user):
            for follow_request in request.user.received_follow_requests.all():
                follow_request.accept()
        return Response(serializer.data)


class ProfileView(APIView):
    """Shows a user's profile. Without a username, the requesting user's own."""

    def get_target(self, request, username=None):
        if username is None:
            return request.user
        return get_object_or_404(User, username=username, is_active=True)

    def profile_response(self, request, target):
        return Response(ProfileSerializer(target, context={"request": request}).data)

    def get(self, request, username=None):
        return self.profile_response(request, self.get_target(request, username))


class FollowView(ProfileView):
    def post(self, request, username):
        target = self.get_target(request, username)
        if target == request.user:
            return Response(
                {"detail": "Du kannst dir nicht selbst folgen."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if requires_follow_request(target) and not follows(request.user, target):
            FollowRequest.objects.get_or_create(follower=request.user, following=target)
        else:
            Follow.objects.get_or_create(follower=request.user, following=target)
        return self.profile_response(request, target)

    def delete(self, request, username):
        target = self.get_target(request, username)
        Follow.objects.filter(follower=request.user, following=target).delete()
        FollowRequest.objects.filter(follower=request.user, following=target).delete()
        return self.profile_response(request, target)


class FriendRequestView(ProfileView):
    def post(self, request, username):
        target = self.get_target(request, username)
        if not (follows(request.user, target) and follows(target, request.user)):
            return Response(
                {"detail": "Freundschaftsanfragen gehen nur, wenn ihr euch gegenseitig folgt."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if are_friends(request.user, target):
            return Response(
                {"detail": "Ihr seid bereits befreundet."}, status=status.HTTP_400_BAD_REQUEST
            )
        FriendRequest.objects.get_or_create(sender=request.user, receiver=target)
        return self.profile_response(request, target)
