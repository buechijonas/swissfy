from django.contrib.auth import get_user_model
from django.db.models import Case, Exists, F, IntegerField, OuterRef, Q, Subquery, Value, When
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserProfile, get_or_create_profile
from accounts.roles import NAME_ORDERING, is_admin, is_moderator, with_role_rank
from main.pagination import NextPagePagination
from moderation.sanctions import suspended_users
from notifications.models import Notification
from notifications.notify import notify, resolve_friend_request, withdraw
from posts.models import Story, StoryLike, StoryView, story_cutoff
from posts.views import serve_image

from .models import Follow, FollowRequest, FriendRequest, Friendship
from .pictures import KINDS, picture_file, sees_private, viewer_relations
from .serializers import (
    PictureSettingsSerializer,
    PrivacySerializer,
    ProfileListSerializer,
    ProfileSerializer,
    StoryViewerSerializer,
    are_friends,
    can_view_profile,
    follows,
    requires_follow_request,
)

User = get_user_model()
Resolution = Notification.Resolution


class ProfileListView(generics.ListAPIView):
    serializer_class = ProfileListSerializer
    pagination_class = NextPagePagination

    def get_users(self):
        return User.objects.filter(is_active=True).exclude(pk=self.request.user.pk)

    def get_queryset(self):
        viewer = self.request.user
        users = self.get_users()
        if not is_admin(viewer):
            users = users.exclude(pk__in=suspended_users())
        query = " ".join(self.request.query_params.get("q", "").split())
        if query:
            users = search(users, query, viewer) if len(query) >= MIN_QUERY_LENGTH else users.none()
        users = with_visibility_ranks(with_viewer_relations(with_role_rank(users), viewer), viewer)
        return users.order_by("lock_rank", "shown_role_rank", *NAME_ORDERING)


def with_visibility_ranks(users, viewer):
    if is_admin(viewer):
        return users.annotate(lock_rank=Value(0), shown_role_rank=F("role_rank"))
    Visibility = UserProfile.Visibility
    viewable = (
        Q(profile__isnull=True)
        | Q(profile__profile_visibility=Visibility.PUBLIC)
        | Q(profile__profile_visibility=Visibility.FOLLOWERS, viewer_follows=True)
        | Q(viewer_is_friend=True)
    )
    return users.annotate(
        lock_rank=Case(
            When(viewable, then=Value(0)), default=Value(1), output_field=IntegerField()
        ),
        shown_role_rank=Case(When(viewable, then=F("role_rank")), default=Value(0)),
    )


MIN_QUERY_LENGTH = 2


def search(users, query, viewer):
    Visibility = UserProfile.Visibility
    names_visible = (
        Q()
        if is_admin(viewer)
        else (
            Q(profile__isnull=True)
            | Q(profile__profile_visibility=Visibility.PUBLIC)
            | Q(
                profile__profile_visibility=Visibility.FOLLOWERS,
                pk__in=Follow.objects.filter(follower=viewer).values("following"),
            )
            | Q(pk__in=Friendship.objects.filter(user=viewer).values("friend"))
        )
    )
    terms = query.split()
    partial = User.objects.all()
    for term in terms:
        by_username = User.objects.filter(username__icontains=term).values("pk")
        by_name = User.objects.filter(
            names_visible, Q(first_name__icontains=term) | Q(last_name__icontains=term)
        ).values("pk")
        partial = partial.filter(pk__in=by_username.union(by_name))

    full_name = Q(pk__in=[])
    for split in range(1, len(terms)):
        first, last = " ".join(terms[:split]), " ".join(terms[split:])
        full_name |= Q(first_name__iexact=first, last_name__iexact=last)
        full_name |= Q(first_name__iexact=last, last_name__iexact=first)
    exact = User.objects.filter(full_name).values("pk")
    return users.filter(pk__in=partial.values("pk").union(exact))


def with_viewer_relations(users, viewer):
    return (
        users.select_related("profile")
        .prefetch_related("groups")
        .annotate(
            viewer_follows=Exists(Follow.objects.filter(follower=viewer, following=OuterRef("pk"))),
            viewer_is_friend=Exists(Friendship.objects.filter(user=viewer, friend=OuterRef("pk"))),
        )
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
        return get_object_or_404(FollowRequest, follower__username=username, following=request.user)

    def post(self, request, username):
        self.get_request(request, username).accept()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, username):
        self.get_request(request, username).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FriendRequestDecisionView(FollowRequestView):
    def get_request(self, request, username):
        return get_object_or_404(FriendRequest, sender__username=username, receiver=request.user)

    def post(self, request, username):
        friend_request = self.get_request(request, username)
        resolve_friend_request(request.user, friend_request.sender, Resolution.ACCEPTED)
        friend_request.accept()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, username):
        friend_request = self.get_request(request, username)
        resolve_friend_request(request.user, friend_request.sender, Resolution.DECLINED)
        friend_request.delete()
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


def picture_settings_response(request, profile):
    return Response(PictureSettingsSerializer(profile, context={"request": request}).data)


def checked_kind(kind):
    if kind not in KINDS:
        raise Http404
    return kind


class PictureSettingsView(APIView):
    parser_classes = [MultiPartParser, JSONParser]

    def get(self, request):
        return picture_settings_response(request, get_or_create_profile(request.user))

    def patch(self, request):
        serializer = PictureSettingsSerializer(
            get_or_create_profile(request.user),
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        return picture_settings_response(request, serializer.save())


class OwnPictureView(APIView):
    def delete(self, request, kind):
        profile = get_or_create_profile(request.user)
        picture_file(profile, checked_kind(kind)).delete()
        return picture_settings_response(request, profile)


def profile_target(request, username):
    users = User.objects.filter(is_active=True)
    if not is_moderator(request.user):
        users = users.filter(~Q(pk__in=suspended_users()) | Q(pk=request.user.pk))
    return get_object_or_404(users, username=username)


def followers_of(user):
    return Follow.objects.filter(following=user).values("follower")


def followed_by(user):
    return Follow.objects.filter(follower=user).values("following")


def friends_of(user):
    return Friendship.objects.filter(user=user).values("friend")


class ConnectionListView(ProfileListView):
    connections = None

    def get_users(self):
        target = profile_target(self.request, self.kwargs["username"])
        if not can_view_profile(self.request.user, target):
            raise PermissionDenied("Dieses Profil ist privat.")
        return User.objects.filter(is_active=True, pk__in=self.connections(target))


class ProfileView(APIView):
    def get_target(self, request, username=None):
        return request.user if username is None else profile_target(request, username)

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
            _, created = Follow.objects.get_or_create(follower=request.user, following=target)
            if created:
                notify(target, Notification.Kind.FOLLOW, actor=request.user)
        return self.profile_response(request, target)

    def delete(self, request, username):
        target = self.get_target(request, username)
        Follow.objects.filter(follower=request.user, following=target).delete()
        withdraw(target, Notification.Kind.FOLLOW, request.user)
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
        _, created = FriendRequest.objects.get_or_create(sender=request.user, receiver=target)
        if created:
            notify(target, Notification.Kind.FRIEND_REQUEST, actor=request.user)
        return self.profile_response(request, target)


class PictureView(ProfileView):
    def get(self, request, username, kind):
        target = self.get_target(request, username)
        profile = get_or_create_profile(target)
        file = picture_file(profile, checked_kind(kind))
        if kind == "private" and not sees_private(
            profile, request.user, viewer_relations(request.user, [target])
        ):
            file = None
        if not file:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return serve_image(file)


class StoryViewerListView(generics.ListAPIView):
    serializer_class = StoryViewerSerializer
    pagination_class = NextPagePagination

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
