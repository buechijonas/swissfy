from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.models import UserProfile, get_or_create_profile
from accounts.roles import is_admin, is_moderator, role_badge
from chats.models import ChatRequest
from main.numbers import compact_number
from posts import images
from posts.models import ContactGroup

from .models import Follow, FollowRequest, FriendRequest, Friendship
from .pictures import KINDS, PictureField, file_url, picture_file

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


def can_view_profile(viewer, user):
    if user == viewer or is_admin(viewer):
        return True
    profile = getattr(user, "profile", None)
    return not profile or is_visible(
        profile.profile_visibility, follows(viewer, user), are_friends(viewer, user)
    )


HIDDEN_LIST_FIELDS = ["first_name", "last_name", "role"]
HIDDEN_PROFILE_FIELDS = [*HIDDEN_LIST_FIELDS, "follower_count", "following_count", "friend_count"]


class ProfileListSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    picture = PictureField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "avatar", "picture", "role"]

    def get_avatar(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.avatar if profile else ""

    def get_role(self, obj):
        return role_badge(obj)

    def to_representation(self, obj):
        data = super().to_representation(obj)
        profile = getattr(obj, "profile", None)
        data["can_view"] = (
            not profile
            or is_admin(self.context["request"].user)
            or is_visible(profile.profile_visibility, obj.viewer_follows, obj.viewer_is_friend)
        )
        if not data["can_view"]:
            for field in HIDDEN_LIST_FIELDS:
                del data[field]
        return data


class ProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    picture = PictureField()
    role = serializers.SerializerMethodField()
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
    can_view_warnings = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "avatar",
            "picture",
            "role",
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
            "can_view_warnings",
        ]

    @property
    def viewer(self):
        return self.context["request"].user

    def get_avatar(self, obj):
        return get_or_create_profile(obj).avatar

    def get_role(self, obj):
        return role_badge(obj)

    def get_can_view_warnings(self, obj):
        return obj == self.viewer or is_moderator(self.viewer)

    def get_follower_count(self, obj):
        return compact_number(obj.followers.count())

    def get_following_count(self, obj):
        return compact_number(obj.following.count())

    def get_friend_count(self, obj):
        return compact_number(obj.friendships.count())

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

        data["can_view"] = (
            data["is_self"]
            or is_admin(self.viewer)
            or is_visible(profile.profile_visibility, data["is_following"], data["is_friend"])
        )
        if not data["can_view"]:
            for field in HIDDEN_PROFILE_FIELDS:
                del data[field]
        elif data["is_self"] or profile.show_birthdate:
            data["birthdate"] = profile.birthdate
        return data


class PrivacySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["profile_visibility", "read_receipts", "chat_requests", "show_birthdate"]


class PictureSettingsSerializer(serializers.ModelSerializer):
    public_picture = serializers.FileField(required=False, write_only=True)
    private_picture = serializers.FileField(required=False, write_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "public_picture",
            "private_picture",
            "private_picture_visibility",
            "private_picture_groups",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["private_picture_groups"].child_relation.queryset = ContactGroup.objects.filter(
            owner=self.context["request"].user
        )

    def compress(self, upload):
        try:
            return images.thumbnail(images.load(upload))
        except images.InvalidImage as error:
            raise serializers.ValidationError(str(error))

    def validate_public_picture(self, upload):
        return self.compress(upload)

    def validate_private_picture(self, upload):
        return self.compress(upload)

    def validate(self, data):
        visibility = data.get("private_picture_visibility")
        if visibility == UserProfile.PictureAudience.GROUPS:
            if not data.get("private_picture_groups"):
                raise serializers.ValidationError(
                    {"private_picture_groups": "Wähle mindestens eine Gruppe."}
                )
        elif visibility:
            data["private_picture_groups"] = []
        return data

    def update(self, profile, data):
        for kind in KINDS:
            if f"{kind}_picture" in data:
                picture_file(profile, kind).delete(save=False)
        return super().update(profile, data)

    def to_representation(self, profile):
        data = super().to_representation(profile)
        for kind in KINDS:
            file = picture_file(profile, kind)
            data[f"{kind}_picture"] = file_url(profile.user, kind, file) if file else None
        return data
