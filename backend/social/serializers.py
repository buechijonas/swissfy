from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.models import UserProfile, get_or_create_profile
from chats.models import ChatRequest

from .models import Follow, FollowRequest, FriendRequest, Friendship

User = get_user_model()


def follows(follower, following):
    return Follow.objects.filter(follower=follower, following=following).exists()


def are_friends(user, other):
    return Friendship.objects.filter(user=user, friend=other).exists()


def requires_follow_request(user):
    return get_or_create_profile(user).profile_visibility != UserProfile.Visibility.PUBLIC


def is_visible(visibility, is_following, is_friend):
    Visibility = UserProfile.Visibility
    return (
        visibility == Visibility.PUBLIC
        or (visibility == Visibility.FOLLOWERS and is_following)
        or is_friend
    )


HIDDEN_LIST_FIELDS = ["first_name", "last_name"]
HIDDEN_PROFILE_FIELDS = [*HIDDEN_LIST_FIELDS, "follower_count", "following_count", "friend_count"]


class ProfileListSerializer(serializers.ModelSerializer):
    """The short form of a profile, for user lists. Expects `profile` to be
    select_related, since not every user has one (e.g. local admins)."""

    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "avatar"]

    def get_avatar(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.avatar if profile else ""

    def to_representation(self, obj):
        data = super().to_representation(obj)
        profile = getattr(obj, "profile", None)
        data["can_view"] = not profile or is_visible(
            profile.profile_visibility, obj.viewer_follows, obj.viewer_is_friend
        )
        if not data["can_view"]:
            for field in HIDDEN_LIST_FIELDS:
                del data[field]
        return data


class ProfileSerializer(serializers.ModelSerializer):
    """A user's public profile, seen by the requesting user (`context["request"]`)."""

    avatar = serializers.SerializerMethodField()
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    friend_count = serializers.SerializerMethodField()
    is_self = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    follows_you = serializers.SerializerMethodField()
    is_friend = serializers.SerializerMethodField()
    friend_request_sent = serializers.SerializerMethodField()
    follow_requested = serializers.SerializerMethodField()
    requires_follow_request = serializers.SerializerMethodField()
    can_chat = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "avatar",
            "follower_count",
            "following_count",
            "friend_count",
            "is_self",
            "is_following",
            "follows_you",
            "is_friend",
            "friend_request_sent",
            "follow_requested",
            "requires_follow_request",
            "can_chat",
        ]

    @property
    def viewer(self):
        return self.context["request"].user

    def get_avatar(self, obj):
        return get_or_create_profile(obj).avatar

    def get_follower_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

    def get_friend_count(self, obj):
        return obj.friendships.count()

    def get_is_self(self, obj):
        return obj == self.viewer

    def get_is_following(self, obj):
        return follows(self.viewer, obj)

    def get_follows_you(self, obj):
        return follows(obj, self.viewer)

    def get_is_friend(self, obj):
        return are_friends(self.viewer, obj)

    def get_friend_request_sent(self, obj):
        return FriendRequest.objects.filter(sender=self.viewer, receiver=obj).exists()

    def get_follow_requested(self, obj):
        return FollowRequest.objects.filter(follower=self.viewer, following=obj).exists()

    def get_requires_follow_request(self, obj):
        return requires_follow_request(obj)

    def get_can_chat(self, obj):
        if obj == self.viewer:
            return False
        if ChatRequest.between(self.viewer, obj):
            return True
        return get_or_create_profile(obj).chat_requests

    def to_representation(self, obj):
        data = super().to_representation(obj)
        profile = get_or_create_profile(obj)

        data["can_view"] = data["is_self"] or is_visible(
            profile.profile_visibility, data["is_following"], data["is_friend"]
        )
        if not data["can_view"]:
            for field in HIDDEN_PROFILE_FIELDS:
                del data[field]
        return data


class PrivacySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["profile_visibility", "read_receipts", "chat_requests"]
