from django.contrib.auth import get_user_model
from rest_framework import serializers

from commons.fields import CompactNumberField
from commons.serializers import BaseModelSerializer
from swissfy.accounts.fields import RoleBadgeField
from swissfy.accounts.models import UserProfile
from swissfy.posts import images
from swissfy.posts.models import ContactGroup
from swissfy.posts.serializers import StoryModelSerializer

from . import library
from .pictures import KINDS, PictureField, file_url, picture_file

User = get_user_model()


HIDDEN_LIST_FIELDS = ["first_name", "last_name", "role"]
HIDDEN_PROFILE_FIELDS = [*HIDDEN_LIST_FIELDS, "follower_count", "following_count", "friend_count"]


class ProfileModelSerializer(BaseModelSerializer):
    class list(BaseModelSerializer.read):
        avatar = serializers.CharField(source="profile.avatar", read_only=True)
        picture = PictureField()
        role = RoleBadgeField()
        can_view = serializers.BooleanField(source="viewer_can_view", read_only=True)
        display_name = serializers.CharField(source="visible_name", read_only=True)
        hidden_fields = HIDDEN_LIST_FIELDS

        class Meta(BaseModelSerializer.read.Meta):
            model = User
            fields = [
                "username",
                "display_name",
                "first_name",
                "last_name",
                "avatar",
                "picture",
                "role",
                "can_view",
            ]

        def to_representation(self, obj):
            data = super().to_representation(obj)
            if not data["can_view"]:
                for field in self.hidden_fields:
                    del data[field]
            return data

    class story_viewer(list):
        liked = serializers.BooleanField(read_only=True)

        class Meta(BaseModelSerializer.read.Meta):
            model = User
            fields = [
                "username",
                "display_name",
                "first_name",
                "last_name",
                "avatar",
                "picture",
                "role",
                "can_view",
                "liked",
            ]

    class read(list):
        follower_count = CompactNumberField()
        following_count = CompactNumberField()
        friend_count = CompactNumberField()
        is_self = serializers.BooleanField(read_only=True)
        is_following = serializers.BooleanField(source="viewer_follows", read_only=True)
        follows_you = serializers.BooleanField(source="follows_viewer", read_only=True)
        is_friend = serializers.BooleanField(source="viewer_is_friend", read_only=True)
        friend_request_sent = serializers.BooleanField(read_only=True)
        follow_requested = serializers.BooleanField(read_only=True)
        requires_follow_request = serializers.BooleanField(
            source="profile.requires_follow_request", read_only=True
        )
        can_chat = serializers.BooleanField(read_only=True)
        can_view_warnings = serializers.BooleanField(read_only=True)
        media = serializers.ReadOnlyField()
        stories = StoryModelSerializer.read(source="visible_stories", many=True, read_only=True)
        hidden_fields = HIDDEN_PROFILE_FIELDS

        class Meta(BaseModelSerializer.read.Meta):
            model = User
            fields = [
                "username",
                "display_name",
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
                "media",
                "stories",
                "can_view",
            ]

        def to_representation(self, obj):
            data = super().to_representation(obj)
            if not data["can_view"]:
                return data
            profile = obj.profile
            data.update(about_data(profile))
            if data["is_self"] or profile.show_birthdate:
                data["birthdate"] = profile.birthdate
            return data


FAVORITE_FIELDS = {f"favorite_{kind}": kind for kind in library.KINDS}


def favorites_data(items):
    return [
        {**item, "cover": f"/api/social/covers/{item['cover']}" if item["cover"] else None}
        for item in items
    ]


def about_data(profile):
    return {
        "biography": profile.biography,
        **{field: favorites_data(items) for field, items in profile.favorites.items()},
    }


class ProfileSettingsModelSerializer:
    class privacy(serializers.ModelSerializer):
        class Meta:
            model = UserProfile
            fields = ["profile_visibility", "read_receipts", "chat_requests", "show_birthdate"]

    class about(serializers.ModelSerializer):
        favorite_movies = serializers.ListField(
            child=serializers.CharField(), max_length=library.MAX_FAVORITES, required=False
        )
        favorite_series = serializers.ListField(
            child=serializers.CharField(), max_length=library.MAX_FAVORITES, required=False
        )
        favorite_games = serializers.ListField(
            child=serializers.CharField(), max_length=library.MAX_FAVORITES, required=False
        )

        class Meta:
            model = UserProfile
            fields = ["biography", *FAVORITE_FIELDS]

        def validate(self, data):
            for field, kind in FAVORITE_FIELDS.items():
                if field not in data:
                    continue
                known = {item["id"]: item for item in self.instance.favorites[field]}
                ids = list(dict.fromkeys(data[field]))
                data[field] = [known.get(id) or library.details(kind, id) for id in ids]
            return data

        def to_representation(self, profile):
            return about_data(profile)

    class pictures(serializers.ModelSerializer):
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
            self.fields["private_picture_groups"].child_relation.queryset = (
                ContactGroup.objects.filter(owner=self.context["request"].user)
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
