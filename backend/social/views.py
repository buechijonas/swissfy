from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Follow, FriendRequest
from .serializers import ProfileSerializer, are_friends, follows

User = get_user_model()


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
        Follow.objects.get_or_create(follower=request.user, following=target)
        return self.profile_response(request, target)

    def delete(self, request, username):
        target = self.get_target(request, username)
        Follow.objects.filter(follower=request.user, following=target).delete()
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
