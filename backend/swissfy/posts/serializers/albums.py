from rest_framework import serializers

from commons.serializers import BaseModelSerializer, UUIDModelSerializer

from ..models import Album, AlbumEntry, Post
from .posts import PostModelSerializer


class AlbumModelSerializer(UUIDModelSerializer):
    class read(UUIDModelSerializer.read):
        cover = serializers.CharField(source="cover_url", read_only=True)
        cover_entry = serializers.UUIDField(read_only=True, allow_null=True)
        is_own = serializers.BooleanField(read_only=True)

        class Meta(UUIDModelSerializer.read.Meta):
            model = Album
            fields = UUIDModelSerializer.read.Meta.fields + [
                "name",
                "cover",
                "cover_entry",
                "created_at",
                "is_own",
            ]

    class write(BaseModelSerializer.write):
        cover = serializers.SlugRelatedField(
            slug_field="uuid", queryset=AlbumEntry.objects.none(), required=False, allow_null=True
        )

        class Meta(BaseModelSerializer.write.Meta):
            model = Album
            fields = ["name", "cover"]

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if self.instance:
                self.fields["cover"].queryset = self.instance.entries.all()


class AlbumEntryModelSerializer(UUIDModelSerializer):
    class read(UUIDModelSerializer.read):
        post = PostModelSerializer.album(read_only=True)

        class Meta(UUIDModelSerializer.read.Meta):
            model = AlbumEntry
            fields = UUIDModelSerializer.read.Meta.fields + ["post", "date", "title"]

    class write(BaseModelSerializer.write):
        post = serializers.SlugRelatedField(slug_field="uuid", queryset=Post.objects.none())

        class Meta(BaseModelSerializer.write.Meta):
            model = AlbumEntry
            fields = ["post", "date", "title"]

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            user = self.context["request"].user
            self.fields["post"].queryset = Post.objects.filter(author=user).media()
