from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from commons.fields import CompactNumberField
from commons.serializers import BaseModelSerializer, UUIDModelSerializer

from .. import hashtags, images, videos
from ..models import Hashtag, Post, PostImage
from .common import (
    AudienceSerializerMixin,
    AuthorModelSerializer,
    HashtagTextField,
    ModeratedSerializerMixin,
    UnavailableSerializer,
)


class UnfiledOrFolderField(serializers.IntegerField):
    def to_internal_value(self, data):
        if data == "none":
            return None
        return super().to_internal_value(data)


class PostImageModelSerializer(BaseModelSerializer):
    class read(BaseModelSerializer.read):
        url = serializers.CharField(read_only=True)
        aspect_ratio = serializers.FloatField(read_only=True)

        class Meta(BaseModelSerializer.read.Meta):
            model = PostImage
            fields = ["url", "aspect_ratio"]


class PostModelSerializer(UUIDModelSerializer):
    class read(ModeratedSerializerMixin, UUIDModelSerializer.read):
        author = AuthorModelSerializer.read(read_only=True)
        images = PostImageModelSerializer.read(many=True, read_only=True)
        video = serializers.CharField(source="video_url", read_only=True)
        thumbnail = serializers.CharField(source="thumbnail_url", read_only=True)
        text_parts = HashtagTextField()
        aspect_ratio = serializers.FloatField(read_only=True)
        list_aspect_ratio = serializers.FloatField(read_only=True)
        like_count = CompactNumberField()
        comment_count = serializers.IntegerField(read_only=True)
        liked = serializers.BooleanField(read_only=True)
        reposted = serializers.BooleanField(read_only=True)
        reposter = serializers.CharField(read_only=True)
        saved = serializers.BooleanField(read_only=True)
        saved_folder = serializers.IntegerField(read_only=True)
        is_own = serializers.BooleanField(read_only=True)

        class Meta(UUIDModelSerializer.read.Meta):
            model = Post
            fields = UUIDModelSerializer.read.Meta.fields + [
                "author",
                "text",
                "text_parts",
                "images",
                "video",
                "video_status",
                "thumbnail",
                "aspect_ratio",
                "list_aspect_ratio",
                "visibility",
                "groups",
                "created_at",
                "like_count",
                "comment_count",
                "liked",
                "reposted",
                "reposter",
                "saved",
                "saved_folder",
                "is_own",
                "hidden",
                "reported",
                "can_report",
            ]

        def to_representation(self, obj):
            data = super().to_representation(obj)
            if not data["is_own"]:
                del data["visibility"]
                del data["groups"]
            return data

    class summary(UUIDModelSerializer.read):
        author = AuthorModelSerializer.read(read_only=True)
        thumbnail = serializers.CharField(source="thumbnail_url", read_only=True)
        comment_count = serializers.IntegerField(read_only=True)

        class Meta(UUIDModelSerializer.read.Meta):
            model = Post
            fields = UUIDModelSerializer.read.Meta.fields + [
                "author",
                "text",
                "thumbnail",
                "created_at",
                "comment_count",
            ]

    class album(UUIDModelSerializer.read):
        author = AuthorModelSerializer.read(read_only=True)
        thumbnail = serializers.CharField(source="thumbnail_url", read_only=True)
        video = serializers.BooleanField(source="has_video", read_only=True)

        class Meta(UUIDModelSerializer.read.Meta):
            model = Post
            fields = UUIDModelSerializer.read.Meta.fields + ["author", "thumbnail", "video"]

    class unavailable(UnavailableSerializer):
        blocked = _("This feed has been blocked.")
        hidden = _("This feed is not visible.")

        class Meta(UnavailableSerializer.Meta):
            model = Post

    class query(serializers.Serializer):
        images = serializers.BooleanField(default=False)
        videos = serializers.BooleanField(default=False)
        media = serializers.BooleanField(default=False)

    class saved_query(serializers.Serializer):
        folder = UnfiledOrFolderField(required=False)

    class audience(AudienceSerializerMixin, BaseModelSerializer.write):
        class Meta(BaseModelSerializer.write.Meta):
            model = Post
            fields = ["visibility", "groups"]
            extra_kwargs = {"visibility": {"required": True}}

        def validate(self, data):
            return self.clean_audience(data)

    class write(AudienceSerializerMixin, BaseModelSerializer.write):
        images = serializers.ListField(
            child=serializers.FileField(), required=False, allow_empty=False, write_only=True
        )
        video = serializers.FileField(required=False, write_only=True)

        class Meta(BaseModelSerializer.write.Meta):
            model = Post
            fields = ["text", "images", "video", "visibility", "groups"]

        def validate_images(self, uploads):
            try:
                return images.compress(uploads)
            except images.InvalidImage as error:
                raise serializers.ValidationError(str(error)) from error

        def validate_video(self, upload):
            try:
                return videos.validate(upload)
            except videos.InvalidVideo as error:
                raise serializers.ValidationError(str(error)) from error

        def validate(self, data):
            if data.get("images") and data.get("video"):
                raise serializers.ValidationError({"video": _("Choose either images or a video.")})
            if (
                not data.get("text", "").strip()
                and not data.get("images")
                and not data.get("video")
            ):
                raise serializers.ValidationError(
                    {"text": _("Write something or choose an image or video.")}
                )
            return self.clean_audience(data)

        def create(self, data):
            files = []
            if "images" in data:
                files, data["thumbnail"], data["image_width"], data["image_height"] = data.pop(
                    "images"
                )
            if "video" in data:
                data["video_upload"] = data.pop("video")
                data["video_status"] = Post.VideoStatus.PROCESSING
            post = super().create({**data, "author": self.context["request"].user})
            hashtags.tag(post)
            PostImage.objects.bulk_create(
                PostImage(post=post, file=file, width=width, height=height, position=position)
                for position, (file, width, height) in enumerate(files)
            )
            return post


class HashtagModelSerializer(BaseModelSerializer):
    class read(BaseModelSerializer.read):
        post_count = CompactNumberField()
        following = serializers.BooleanField(read_only=True)

        class Meta(BaseModelSerializer.read.Meta):
            model = Hashtag
            fields = ["name", "post_count", "following"]
