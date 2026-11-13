from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import (
    Case,
    CharField,
    Exists,
    F,
    IntegerField,
    Max,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
)
from django.utils import timezone

from commons.models import BaseModel, BaseQuerySet, boolean, count_of
from swissfy.accounts.models import UserProfile
from swissfy.accounts.roles import NAME_ORDERING, is_admin, is_moderator, with_role_rank
from swissfy.moderation.models import LOCKED_FOREVER, WARNING_EXPIRY, Suspension, Warning

Visibility = UserProfile.Visibility
PictureAudience = UserProfile.PictureAudience
MIN_QUERY_LENGTH = 2


class Follow(BaseModel):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following"
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="unique_follow"),
            models.CheckConstraint(condition=~Q(follower=F("following")), name="no_follow_of_self"),
        ]

    def __str__(self):
        return f"{self.follower} follows {self.following}"


class FollowRequest(BaseModel):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_follow_requests"
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_follow_requests",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="unique_follow_request"),
            models.CheckConstraint(
                condition=~Q(follower=F("following")), name="no_follow_request_to_self"
            ),
        ]

    def accept(self):
        Follow.objects.get_or_create(follower=self.follower, following=self.following)
        self.delete()

    def __str__(self):
        return f"{self.follower} -> {self.following}"


class FriendRequest(BaseModel):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_friend_requests"
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_friend_requests",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["sender", "receiver"], name="unique_friend_request"),
            models.CheckConstraint(
                condition=~Q(sender=F("receiver")), name="no_friend_request_to_self"
            ),
        ]

    def accept(self):
        Friendship.objects.get_or_create(user=self.sender, friend=self.receiver)
        Friendship.objects.get_or_create(user=self.receiver, friend=self.sender)
        self.delete()

    def __str__(self):
        return f"{self.sender} -> {self.receiver}"


class Friendship(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="friendships"
    )
    friend = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "friend"], name="unique_friendship"),
            models.CheckConstraint(condition=~Q(user=F("friend")), name="no_friendship_with_self"),
        ]

    def __str__(self):
        return f"{self.user} <-> {self.friend}"


class Block(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocks"
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocked_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "blocked"], name="unique_block"),
            models.CheckConstraint(condition=~Q(user=F("blocked")), name="no_block_of_self"),
        ]

    def __str__(self):
        return f"{self.user} blocks {self.blocked}"


class Nickname(BaseModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="given_nicknames"
    )
    target = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    nickname = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["owner", "target"], name="unique_nickname"),
        ]

    def __str__(self):
        return f"{self.owner} -> {self.target}: {self.nickname}"


def viewable_by_relations():
    return (
        Q(profile__profile_visibility=Visibility.PUBLIC)
        | Q(profile__profile_visibility=Visibility.FOLLOWERS, viewer_follows=True)
        | Q(viewer_is_friend=True)
    )


def private_picture_shared():
    return (
        Q(profile__private_picture_visibility=PictureAudience.FOLLOWERS, viewer_follows=True)
        | Q(profile__private_picture_visibility=PictureAudience.FRIENDS, viewer_is_friend=True)
        | Q(
            profile__private_picture_visibility=PictureAudience.GROUPS, viewer_in_picture_group=True
        )
    )


def shown_picture(private_visible):
    return Case(
        When(private_visible & ~Q(profile__private_picture=""), then=Value("private")),
        When(~Q(profile__public_picture=""), then=Value("public")),
        default=Value(None),
        output_field=CharField(),
    )


def latest(queryset, field):
    values = queryset.order_by().values("user").annotate(latest=Max(field)).values("latest")
    return Subquery(values[:1])


class MemberQuerySet(BaseQuerySet):
    def apply_acl(self, user, action="read"):
        members = self.filter(is_active=True)
        if is_moderator(user):
            return members
        suspended = Suspension.objects.running().values("user")
        return members.filter(~Q(pk__in=suspended) | Q(pk=user.pk))

    def listed_for(self, viewer):
        members = self.filter(is_active=True)
        if is_admin(viewer):
            return members
        return members.exclude(pk__in=Suspension.objects.running().values("user"))

    def connected_to(self, kind, user):
        connections = {
            "followers": Follow.objects.filter(following=user).values("follower"),
            "following": Follow.objects.filter(follower=user).values("following"),
            "friends": Friendship.objects.filter(user=user).values("friend"),
        }
        return self.filter(pk__in=connections[kind])

    def annotate_visibility(self, viewer):
        if viewer.is_anonymous:
            return self.annotate(
                viewer_follows=Value(False),
                viewer_is_friend=Value(False),
                viewer_can_view=boolean(Q(profile__profile_visibility=Visibility.PUBLIC)),
                viewer_sees_private_picture=Value(False),
                shown_picture=Value(None, output_field=CharField()),
            )
        member = OuterRef("pk")
        members = self.annotate(
            viewer_follows=Exists(Follow.objects.filter(follower=viewer, following=member)),
            viewer_is_friend=Exists(Friendship.objects.filter(user=viewer, friend=member)),
            viewer_in_picture_group=Exists(
                UserProfile.objects.filter(user=member, private_picture_groups__members=viewer)
            ),
        )
        if is_admin(viewer):
            members = members.annotate(
                viewer_can_view=Value(True), viewer_sees_private_picture=Value(True)
            )
        else:
            members = members.annotate(
                viewer_can_view=boolean(viewable_by_relations() | Q(pk=viewer.pk)),
                viewer_sees_private_picture=boolean(private_picture_shared() | Q(pk=viewer.pk)),
            )
        return members.annotate(shown_picture=shown_picture(Q(viewer_sees_private_picture=True)))

    def with_viewer_relations(self, viewer):
        return self.select_related("profile").prefetch_related("groups").annotate_visibility(viewer)

    def annotate_profile_details(self, viewer):
        warnings_visible = Value(True) if is_moderator(viewer) else boolean(Q(pk=viewer.pk))
        member = OuterRef("pk")
        return self.with_viewer_relations(viewer).annotate(
            follower_count=count_of(Follow.objects.all(), "following"),
            following_count=count_of(Follow.objects.all(), "follower"),
            friend_count=count_of(Friendship.objects.all(), "user"),
            is_self=boolean(Q(pk=viewer.pk)),
            follows_viewer=Exists(Follow.objects.filter(follower=member, following=viewer)),
            friend_request_sent=Exists(
                FriendRequest.objects.filter(sender=viewer, receiver=member)
            ),
            follow_requested=Exists(
                FollowRequest.objects.filter(follower=viewer, following=member)
            ),
            can_view_warnings=warnings_visible,
        )

    def ranked_for(self, viewer):
        viewable = Q(viewer_can_view=True)
        return (
            with_role_rank(self)
            .with_viewer_relations(viewer)
            .annotate(
                lock_rank=Case(
                    When(viewable, then=Value(0)), default=Value(1), output_field=IntegerField()
                ),
                shown_role_rank=Case(When(viewable, then=F("role_rank")), default=Value(0)),
            )
            .order_by("lock_rank", "shown_role_rank", *NAME_ORDERING)
        )

    def search(self, query, viewer):
        query = " ".join(query.split())
        if not query:
            return self
        if len(query) < MIN_QUERY_LENGTH:
            return self.none()
        terms = query.split()
        matches = self.partial_matches(terms, viewer).union(self.full_name_matches(terms))
        return self.filter(pk__in=matches)

    def partial_matches(self, terms, viewer):
        visible_names = Member.objects.annotate_visibility(viewer).filter(viewer_can_view=True)
        matches = Member.objects.all()
        for term in terms:
            by_username = Member.objects.filter(username__icontains=term).values("pk")
            by_name = visible_names.filter(
                Q(first_name__icontains=term) | Q(last_name__icontains=term)
            ).values("pk")
            matches = matches.filter(pk__in=by_username.union(by_name))
        return matches.values("pk")

    def full_name_matches(self, terms):
        full_name = Q(pk__in=[])
        for split in range(1, len(terms)):
            first, last = " ".join(terms[:split]), " ".join(terms[split:])
            full_name |= Q(first_name__iexact=first, last_name__iexact=last)
            full_name |= Q(first_name__iexact=last, last_name__iexact=first)
        return Member.objects.filter(full_name).values("pk")

    def with_role_lock(self, now=None):
        now = now or timezone.now()
        suspensions = Suspension.objects.filter(user=OuterRef("pk"))
        warnings = Warning.objects.filter(user=OuterRef("pk")).active(now)
        return self.annotate(
            has_suspension=Exists(suspensions),
            locked_forever=Exists(suspensions.filter(ends_at__isnull=True)),
            latest_suspension_end=latest(suspensions.filter(ends_at__gt=now), "ends_at"),
            latest_warning_at=latest(warnings, "created_at"),
        )

    def can_view(self, viewer, member):
        members = self.filter(pk=member.pk).annotate_visibility(viewer)
        return members.values_list("viewer_can_view", flat=True).get()


class Member(get_user_model()):
    objects = MemberQuerySet.as_manager()

    class Meta:
        proxy = True

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    @property
    def visible_name(self):
        return self.display_name if self.viewer_can_view else self.username

    @property
    def story_seen(self):
        return self.has_story and not self.has_unseen_story

    @property
    def media(self):
        return {"pictures": self.has_pictures, "reels": self.has_reels}

    @property
    def role_lock(self):
        if not self.has_suspension:
            return None
        if self.locked_forever:
            return LOCKED_FOREVER
        warning_expiry = self.latest_warning_at and self.latest_warning_at + WARNING_EXPIRY
        return max(filter(None, [self.latest_suspension_end, warning_expiry]), default=None)
