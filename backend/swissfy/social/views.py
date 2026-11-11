from django.db.models import Exists, OuterRef, Subquery
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response

from commons.exceptions import BadRequest
from commons.views import BaseViewSet
from main.pagination import NextPagePagination
from swissfy.chats.models import annotate_chat_availability
from swissfy.posts.models import Story, StoryLike, StoryView, story_cutoff
from swissfy.posts.views.media import serve_image

from . import library, relations
from .models import FollowRequest, FriendRequest, Member
from .pictures import KINDS, picture_file, sees_private, viewer_relations
from .serializers import (
    ProfileModelSerializer,
    ProfileSettingsModelSerializer,
    favorites_data,
)

CONNECTIONS = {"followers", "following", "friends"}
LIST_ACTIONS = {"list", *CONNECTIONS}


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
        viewer = self.request.user
        if self.action == "list":
            return self.ranked(Member.objects.exclude(pk=viewer.pk))
        if self.action in CONNECTIONS:
            return self.ranked(Member.objects.connected_to(self.action, self.connected()))
        return annotate_chat_availability(Member.objects.annotate_profile_details(viewer), viewer)

    def ranked(self, members):
        viewer = self.request.user
        query = self.request.query_params.get("q", "")
        return members.listed_for(viewer).search(query, viewer).ranked_for(viewer)

    def connected(self):
        target = self.get_object()
        if not Member.objects.can_view(self.request.user, target):
            raise PermissionDenied("Dieses Profil ist privat.")
        return target

    def get_object(self):
        members = Member.objects.apply_acl(self.request.user)
        return get_object_or_404(members, username=self.kwargs["username"])

    def respond(self, user):
        user = self.get_queryset().get(pk=user.pk)
        return Response(
            ProfileModelSerializer.read(user, context=self.get_serializer_context()).data
        )

    def retrieve(self, request, *args, **kwargs):
        return self.respond(self.get_object())

    @action(detail=False)
    def me(self, request):
        return self.respond(request.user)

    @action(detail=True)
    def followers(self, request, username):
        return self.list(request)

    @action(detail=True)
    def following(self, request, username):
        return self.list(request)

    @action(detail=True)
    def friends(self, request, username):
        return self.list(request)

    @action(detail=True, methods=["post"])
    def follow(self, request, username):
        target = self.get_object()
        if target == request.user:
            raise BadRequest("Du kannst dir nicht selbst folgen.")
        relations.follow(request.user, target)
        return self.respond(target)

    @follow.mapping.delete
    def unfollow(self, request, username):
        target = self.get_object()
        relations.unfollow(request.user, target)
        return self.respond(target)

    @action(detail=True, methods=["post"], url_path="friend-request")
    def friend_request(self, request, username):
        target = self.get_object()
        relations.send_friend_request(request.user, target)
        return self.respond(target)

    @action(detail=True, url_path="pictures/<str:kind>")
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

    def edit(self, serializer_class):
        serializer = serializer_class(
            self.profile,
            data=self.request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer

    @action(detail=False)
    def privacy(self, request):
        return Response(ProfileSettingsModelSerializer.privacy(self.profile).data)

    @privacy.mapping.patch
    def update_privacy(self, request):
        serializer = self.edit(ProfileSettingsModelSerializer.privacy)
        if not serializer.instance.requires_follow_request:
            relations.accept_open_follow_requests(request.user)
        return Response(serializer.data)

    @action(detail=False)
    def about(self, request):
        return Response(ProfileSettingsModelSerializer.about(self.profile).data)

    @about.mapping.patch
    def update_about(self, request):
        return Response(self.edit(ProfileSettingsModelSerializer.about).data)

    @action(detail=False, url_path="follow-requests")
    def follow_requests(self, request):
        users = (
            Member.objects.filter(is_active=True, sent_follow_requests__following=request.user)
            .with_viewer_relations(request.user)
            .order_by("sent_follow_requests__created_at")
        )
        context = self.get_serializer_context()
        return Response(ProfileModelSerializer.list(users, many=True, context=context).data)

    @action(detail=False, methods=["post", "delete"], url_path="follow-requests/<str:username>")
    def decide_follow_request(self, request, username):
        follow_request = get_object_or_404(
            FollowRequest, follower__username=username, following=request.user
        )
        relations.decide_follow_request(follow_request, accepted=request.method == "POST")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post", "delete"], url_path="friend-requests/<str:username>")
    def decide_friend_request(self, request, username):
        friend_request = get_object_or_404(
            FriendRequest, sender__username=username, receiver=request.user
        )
        relations.decide_friend_request(friend_request, accepted=request.method == "POST")
        return Response(status=status.HTTP_204_NO_CONTENT)


class OwnPictureViewSet(BaseViewSet):
    parser_classes = [MultiPartParser, JSONParser]

    @property
    def profile(self):
        return self.request.user.profile

    @action(detail=False)
    def pictures(self, request):
        context = self.get_serializer_context()
        return Response(ProfileSettingsModelSerializer.pictures(self.profile, context=context).data)

    @pictures.mapping.patch
    def update_pictures(self, request):
        serializer = ProfileSettingsModelSerializer.pictures(
            self.profile, data=request.data, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.pictures(request)

    @action(detail=False, methods=["delete"], url_path="pictures/<str:kind>")
    def delete_picture(self, request, kind):
        picture_file(self.profile, checked_kind(kind)).delete()
        return self.pictures(request)


class LibraryViewSet(BaseViewSet):
    @action(detail=False, url_path="library/<str:kind>")
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
        users = Member.objects.filter(pk__in=views.values("user")).exclude(pk=self.request.user.pk)
        return (
            users.with_viewer_relations(self.request.user)
            .annotate(
                viewed_at=Subquery(views.values("created_at")),
                liked=Exists(StoryLike.objects.filter(story=story, user=OuterRef("pk"))),
            )
            .order_by("-viewed_at")
        )
