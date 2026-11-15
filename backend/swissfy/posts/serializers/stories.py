from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from commons.fields import CompactNumberField
from commons.serializers import BaseModelSerializer, UUIDModelSerializer

from .. import images
from ..models import Post, Story
from .common import AudienceSerializerMixin


class StoryModelSerializer(UUIDModelSerializer):
    class read(UUIDModelSerializer.read):
        image = serializers.CharField(source="image_url", read_only=True)
        expires_at = serializers.DateTimeField(read_only=True)
        is_own = serializers.BooleanField(read_only=True)
        liked = serializers.BooleanField(read_only=True)
        like_count = CompactNumberField()
        view_count = CompactNumberField()
        seen = serializers.BooleanField(read_only=True)

        class Meta(UUIDModelSerializer.read.Meta):
            model = Story
            fields = UUIDModelSerializer.read.Meta.fields + [
                "image",
                "text",
                "created_at",
                "expires_at",
                "is_own",
                "liked",
                "like_count",
                "view_count",
                "seen",
            ]

    class write(AudienceSerializerMixin, BaseModelSerializer.write):
        image = serializers.FileField(write_only=True)

        class Meta(BaseModelSerializer.write.Meta):
            model = Story
            fields = ["image", "text", "visibility", "groups"]

        def validate_image(self, upload):
            try:
                files, *_ = images.compress([upload])
            except images.InvalidImage as error:
                raise serializers.ValidationError(str(error))
            return files[0][0]

        def validate(self, data):
            if data.get("visibility") == Post.Visibility.GLOBAL:
                raise serializers.ValidationError(
                    {"visibility": _("Stories können nicht global sein.")}
                )
            return self.clean_audience(data)

        def create(self, data):
            return super().create({**data, "author": self.context["request"].user})
