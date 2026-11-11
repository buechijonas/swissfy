from django.contrib.auth import get_user_model
from django.db.models import (
    BooleanField,
    Case,
    Exists,
    ExpressionWrapper,
    F,
    IntegerField,
    OuterRef,
    Q,
    Value,
    When,
)
from django.shortcuts import get_object_or_404

from swissfy.accounts.models import UserProfile
from swissfy.accounts.roles import is_admin, is_moderator
from swissfy.chats.models import ChatRequest
from swissfy.moderation.sanctions import suspended_users
from swissfy.posts.models import count_of

from .models import Follow, FollowRequest, FriendRequest, Friendship

User = get_user_model()
Visibility = UserProfile.Visibility

MIN_QUERY_LENGTH = 2


def boolean(condition):
    return ExpressionWrapper(condition, output_field=BooleanField())


def viewable_by_relations():
    return (
        Q(profile__profile_visibility=Visibility.PUBLIC)
        | Q(profile__profile_visibility=Visibility.FOLLOWERS, viewer_follows=True)
        | Q(viewer_is_friend=True)
    )


def with_viewer_relations(users, viewer):
    users = (
        users.select_related("profile")
        .prefetch_related("groups")
        .annotate(
            viewer_follows=Exists(Follow.objects.filter(follower=viewer, following=OuterRef("pk"))),
            viewer_is_friend=Exists(Friendship.objects.filter(user=viewer, friend=OuterRef("pk"))),
        )
    )
    if is_admin(viewer):
        return users.annotate(viewer_can_view=Value(True))
    return users.annotate(viewer_can_view=boolean(viewable_by_relations() | Q(pk=viewer.pk)))


def with_profile_details(users, viewer):
    can_view_warnings = Value(True) if is_moderator(viewer) else boolean(Q(pk=viewer.pk))
    return (
        with_viewer_relations(users, viewer)
        .annotate(
            follower_count=count_of(Follow.objects, "following"),
            following_count=count_of(Follow.objects, "follower"),
            friend_count=count_of(Friendship.objects, "user"),
            is_self=boolean(Q(pk=viewer.pk)),
            follows_viewer=Exists(Follow.objects.filter(follower=OuterRef("pk"), following=viewer)),
            friend_request_sent=Exists(
                FriendRequest.objects.filter(sender=viewer, receiver=OuterRef("pk"))
            ),
            follow_requested=Exists(
                FollowRequest.objects.filter(follower=viewer, following=OuterRef("pk"))
            ),
            has_chat_request=Exists(ChatRequest.objects.between(viewer, OuterRef("pk"))),
        )
        .annotate(
            can_chat=boolean(
                ~Q(pk=viewer.pk) & (Q(has_chat_request=True) | Q(profile__chat_requests=True))
            ),
            can_view_warnings=can_view_warnings,
        )
    )


def with_visibility_ranks(users, viewer):
    if is_admin(viewer):
        return users.annotate(lock_rank=Value(0), shown_role_rank=F("role_rank"))
    viewable = viewable_by_relations()
    return users.annotate(
        lock_rank=Case(
            When(viewable, then=Value(0)), default=Value(1), output_field=IntegerField()
        ),
        shown_role_rank=Case(When(viewable, then=F("role_rank")), default=Value(0)),
    )


def names_visible_to(viewer):
    if is_admin(viewer):
        return Q()
    return (
        Q(profile__profile_visibility=Visibility.PUBLIC)
        | Q(
            profile__profile_visibility=Visibility.FOLLOWERS,
            pk__in=Follow.objects.filter(follower=viewer).values("following"),
        )
        | Q(pk__in=Friendship.objects.filter(user=viewer).values("friend"))
    )


def partial_matches(terms, viewer):
    names_visible = names_visible_to(viewer)
    matches = User.objects.all()
    for term in terms:
        by_username = User.objects.filter(username__icontains=term).values("pk")
        by_name = User.objects.filter(
            names_visible, Q(first_name__icontains=term) | Q(last_name__icontains=term)
        ).values("pk")
        matches = matches.filter(pk__in=by_username.union(by_name))
    return matches.values("pk")


def full_name_matches(terms):
    full_name = Q(pk__in=[])
    for split in range(1, len(terms)):
        first, last = " ".join(terms[:split]), " ".join(terms[split:])
        full_name |= Q(first_name__iexact=first, last_name__iexact=last)
        full_name |= Q(first_name__iexact=last, last_name__iexact=first)
    return User.objects.filter(full_name).values("pk")


def search(users, query, viewer):
    query = " ".join(query.split())
    if not query:
        return users
    if len(query) < MIN_QUERY_LENGTH:
        return users.none()
    terms = query.split()
    return users.filter(pk__in=partial_matches(terms, viewer).union(full_name_matches(terms)))


def visible_users(viewer):
    users = User.objects.filter(is_active=True)
    if is_moderator(viewer):
        return users
    return users.filter(~Q(pk__in=suspended_users()) | Q(pk=viewer.pk))


def profile_target(viewer, username):
    return get_object_or_404(visible_users(viewer), username=username)


def can_view_profile(viewer, user):
    if user == viewer or is_admin(viewer):
        return True
    following = Follow.objects.filter(follower=viewer, following=user).exists()
    friends = Friendship.objects.filter(user=viewer, friend=user).exists()
    return user.profile.visible_with(following, friends)


CONNECTIONS = {
    "followers": lambda user: Follow.objects.filter(following=user).values("follower"),
    "following": lambda user: Follow.objects.filter(follower=user).values("following"),
    "friends": lambda user: Friendship.objects.filter(user=user).values("friend"),
}
