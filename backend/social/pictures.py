from pathlib import PurePath
from urllib.parse import quote

from rest_framework import serializers

from accounts.models import UserProfile
from accounts.roles import is_admin

from .models import Follow, Friendship

KINDS = ["public", "private"]
Audience = UserProfile.PictureAudience


def viewer_relations(viewer, users=None):
    following = Follow.objects.filter(follower=viewer)
    friends = Friendship.objects.filter(user=viewer)
    groups = UserProfile.objects.filter(private_picture_groups__members=viewer)
    if users is not None:
        following = following.filter(following__in=users)
        friends = friends.filter(friend__in=users)
        groups = groups.filter(user__in=users)
    return {
        "following": set(following.values_list("following_id", flat=True)),
        "friends": set(friends.values_list("friend_id", flat=True)),
        "picture_groups": set(groups.values_list("user_id", flat=True)),
    }


def cached_relations(context):
    if "viewer_relations" not in context:
        context["viewer_relations"] = viewer_relations(context["request"].user)
    return context["viewer_relations"]


def sees_private(profile, viewer, relations):
    if profile.user_id == viewer.pk or is_admin(viewer):
        return True
    audience = {
        Audience.FOLLOWERS: relations["following"],
        Audience.FRIENDS: relations["friends"],
        Audience.GROUPS: relations["picture_groups"],
    }
    return profile.user_id in audience[profile.private_picture_visibility]


def picture_file(profile, kind):
    return getattr(profile, f"{kind}_picture")


def file_url(user, kind, file):
    version = PurePath(file.name).stem
    return f"/api/social/profiles/{quote(user.username)}/pictures/{kind}/?v={version}"


def picture_url(user, context):
    profile = getattr(user, "profile", None)
    if profile is None:
        return None
    if profile.private_picture and sees_private(
        profile, context["request"].user, cached_relations(context)
    ):
        return file_url(user, "private", profile.private_picture)
    if profile.public_picture:
        return file_url(user, "public", profile.public_picture)
    return None


class PictureField(serializers.Field):
    def __init__(self, **kwargs):
        super().__init__(source="*", read_only=True, **kwargs)

    def to_representation(self, user):
        return picture_url(user, self.context)
