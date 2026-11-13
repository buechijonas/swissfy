from pathlib import PurePath

from django.urls import reverse
from rest_framework import serializers

KINDS = ["public", "private"]


def picture_file(profile, kind):
    return profile.pictures[kind]


def file_url(user, kind, file):
    url = reverse("profiles-picture", kwargs={"username": user.username, "kind": kind})
    return f"{url}?v={PurePath(file.name).stem}"


class PictureField(serializers.Field):
    def __init__(self, **kwargs):
        super().__init__(source="*", read_only=True, **kwargs)

    def to_representation(self, user):
        kind = user.shown_picture
        return file_url(user, kind, picture_file(user.profile, kind)) if kind else None
