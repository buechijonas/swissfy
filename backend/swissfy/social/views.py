from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Subquery
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response

from commons.views import BaseViewSet
from main.pagination import NextPagePagination
from swissfy.accounts.roles import NAME_ORDERING, is_admin, with_role_rank
from swissfy.moderation.sanctions import suspended_users
from swissfy.posts.models import Story, StoryLike, StoryView, story_cutoff
from swissfy.posts.views.media import serve_image

from . import library
from .models import FollowRequest, FriendRequest
from .pictures import KINDS, picture_file, sees_private, viewer_relations
from .relations import (
    accept_open_follow_requests,
    decide_follow_request,
    decide_friend_request,
    follow,
    friend_request_error,
    send_friend_request,
    unfollow,
)
from .serializers import (
    AboutSerializer,
    PictureSettingsSerializer,
    PrivacySerializer,
    ProfileModelSerializer,
    favorites_data,
)
from .users import (
    CONNECTIONS,
    can_view_profile,
    profile_target,
    search,
    with_profile_details,
    with_viewer_relations,
    with_visibility_ranks,
)

User = get_user_model()

LIST_ACTIONS = {"list", "connections"}


def checked_kind(kind):
    if kind not in KINDS:
        raise Http404
    return kind


class ProfileViewSet(BaseViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    serializer_class = ProfileModelSerializer
    pagination_class = NextPagePagination
    lookup_field = "username"

    def get_serializer_class(self):
        if self.action in LIST_ACTIONS:
            return ProfileModelSerializer.list
        return ProfileModelSerializer.read

    def get_queryset(self):
        if self.action == "list":
            users = User.objects.filter(is_active=True).exclude(pk=self.request.user.pk)
            return self.ranked(users)
        if self.action == "connections":
            return self.ranked(self.connected_users())
        return with_profile_details(User.objects.all(), self.request.user)

    def ranked(self, users):
        viewer = self.request.user
        if not is_admin(viewer):
            users = users.exclude(pk__in=suspended_users())
        users = search(users, self.request.query_params.get("q", ""), viewer)
        users = with_visibility_ranks(with_viewer_relations(with_role_rank(users), viewer), viewer)
        return users.order_by("lock_rank", "shown_role_rank", *NAME_ORDERING)

    def connected_users(self):
        target = profile_target(self.request.user, self.kwargs["username"])
        if not can_view_profile(self.request.user, target):
            raise PermissionDenied("Dieses Profil ist privat.")
        connected = CONNECTIONS[self.kwargs["kind"]](target)
        return User.objects.filter(is_active=True, pk__in=connected)

    def get_object(self):
        return profile_target(self.request.user, self.kwargs["username"])

    def respond(self, user):
        user = self.get_queryset().get(pk=user.pk)
        return Response(
            ProfileModelSerializer.read(user, context=self.get_serializer_context()).data
        )

    def retrieve(self, request, *args, **kwargs):
        return self.respond(self.get_object())

    def me(self, request):
        return self.respond(request.user)

    def connections(self, request, username, kind):
        return self.list(request)

    def follow(self, request, username):
        target = self.get_object()
        if target == request.user:
            return Response(
                {"detail": "Du kannst dir nicht selbst folgen."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        follow(request.user, target)
        return self.respond(target)

    def unfollow(self, request, username):
        target = self.get_object()
        unfollow(request.user, target)
        return self.respond(target)

    def friend_request(self, request, username):
        target = self.get_object()
        error = friend_request_error(request.user, target)
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
        send_friend_request(request.user, target)
        return self.respond(target)

    def picture(self, request, username, kind):
        target = self.get_object()
        file = picture_file(target.profile, checked_kind(kind))
        if kind == "private" and not sees_private(
            target.profile, request.user, viewer_relations(request.user, [target])
        ):
            file = None
        if not file:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return serve_image(file)


class OwnProfileViewSet(BaseViewSet):
    @property
    def profile(self):
        return self.request.user.profile

    def edit(self, serializer_class, **kwargs):
        serializer = serializer_class(
            self.profile,
            data=self.request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        return serializer, serializer.save()

    def privacy(self, request):
        return Response(PrivacySerializer(self.profile).data)

    def update_privacy(self, request):
        serializer, profile = self.edit(PrivacySerializer)
        if not profile.requires_follow_request:
            accept_open_follow_requests(request.user)
        return Response(serializer.data)

    def about(self, request):
        return Response(AboutSerializer(self.profile).data)

    def update_about(self, request):
        _, profile = self.edit(AboutSerializer)
        return Response(AboutSerializer(profile).data)

    def follow_requests(self, request):
        users = User.objects.filter(
            is_active=True, sent_follow_requests__following=request.user
        ).order_by("sent_follow_requests__created_at")
        users = with_viewer_relations(users, request.user)
        context = self.get_serializer_context()
        return Response(ProfileModelSerializer.list(users, many=True, context=context).data)

    def decide_follow_request(self, request, username):
        follow_request = get_object_or_404(
            FollowRequest, follower__username=username, following=request.user
        )
        decide_follow_request(follow_request, accepted=request.method == "POST")
        return Response(status=status.HTTP_204_NO_CONTENT)

    def decide_friend_request(self, request, username):
        friend_request = get_object_or_404(
            FriendRequest, sender__username=username, receiver=request.user
        )
        decide_friend_request(friend_request, accepted=request.method == "POST")
        return Response(status=status.HTTP_204_NO_CONTENT)


class OwnPictureViewSet(OwnProfileViewSet):
    parser_classes = [MultiPartParser, JSONParser]

    def pictures(self, request):
        context = self.get_serializer_context()
        return Response(PictureSettingsSerializer(self.profile, context=context).data)

    def update_pictures(self, request):
        self.edit(PictureSettingsSerializer)
        return self.pictures(request)

    def delete_picture(self, request, kind):
        picture_file(self.profile, checked_kind(kind)).delete()
        return self.pictures(request)


class LibraryViewSet(BaseViewSet):
    def search(self, request, kind):
        if kind not in library.KINDS:
            raise Http404
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response({"results": []})
        return Response({"results": favorites_data(library.search(kind, query))})

    def cover(self, request, path):
        cover = library.fetch_cover(path)
        if not cover:
            raise Http404
        content, content_type = cover
        response = HttpResponse(content, content_type=content_type)
        response["Cache-Control"] = "private, max-age=31536000, immutable"
        return response


class StoryViewerViewSet(BaseViewSet, mixins.ListModelMixin):
    pagination_class = NextPagePagination

    def get_serializer_class(self):
        return ProfileModelSerializer.story_viewer

    def get_queryset(self):
        stories = Story.objects.filter(author=self.request.user, created_at__gte=story_cutoff())
        story = get_object_or_404(stories, uuid=self.kwargs["uuid"])
        views = StoryView.objects.filter(story=story, user=OuterRef("pk"))
        users = User.objects.filter(pk__in=views.values("user")).exclude(pk=self.request.user.pk)
        users = users.annotate(
            viewed_at=Subquery(views.values("created_at")),
            liked=Exists(StoryLike.objects.filter(story=story, user=OuterRef("pk"))),
        )
        return with_viewer_relations(users, self.request.user).order_by("-viewed_at")
