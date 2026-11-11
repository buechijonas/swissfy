from django.contrib.auth import get_user_model
from rest_framework import serializers

from commons.fields import CompactNumberField
from commons.serializers import BaseModelSerializer, UUIDModelSerializer
from main.numbers import compact_number
from swissfy.accounts.models import UserProfile
from swissfy.accounts.roles import is_admin, is_moderator, outranks, role_badge
from swissfy.social.pictures import PictureField, cached_relations

from . import hashtags, images, videos
from .models import (
    Album,
    AlbumEntry,
    Comment,
    CommentVote,
    ContactGroup,
    Hashtag,
    Post,
    PostImage,
    SavedFolder,
    Story,
)

User = get_user_model()


class AuthorModelSerializer(BaseModelSerializer):
    class read(BaseModelSerializer.read):
        avatar = serializers.CharField(source="profile.avatar", read_only=True)
        picture = PictureField()
        role = serializers.SerializerMethodField()
        has_story = serializers.SerializerMethodField()
        story_seen = serializers.SerializerMethodField()

        class Meta(BaseModelSerializer.read.Meta):
            model = User
            fields = [
                "username",
                "first_name",
                "last_name",
                "avatar",
                "picture",
                "role",
                "has_story",
                "story_seen",
            ]

        def get_role(self, obj):
            return role_badge(obj) if self.profile_visible(obj) else None

        def story_authors(self):
            if "story_authors" not in self.context:
                viewer = self.context["request"].user
                if viewer.is_anonymous:
                    return set(), set()
                stories = Story.objects.apply_acl(viewer)
                unseen = stories.exclude(views__user=viewer)
                self.context["story_authors"] = (
                    set(stories.values_list("author_id", flat=True)),
                    set(unseen.values_list("author_id", flat=True)),
                )
            return self.context["story_authors"]

        def get_has_story(self, obj):
            return obj.pk in self.story_authors()[0]

        def get_story_seen(self, obj):
            authors, unseen = self.story_authors()
            return obj.pk in authors and obj.pk not in unseen

        def profile_visible(self, obj):
            viewer = self.context["request"].user
            if obj == viewer or is_admin(viewer):
                return True
            relations = cached_relations(self.context)
            visibility = obj.profile.profile_visibility
            Visibility = UserProfile.Visibility
            return (
                visibility == Visibility.PUBLIC
                or (visibility == Visibility.FOLLOWERS and obj.pk in relations["following"])
                or obj.pk in relations["friends"]
            )


class ModeratedSerializerMixin(serializers.Serializer):
    hidden = serializers.BooleanField(source="is_hidden", read_only=True)
    reported = serializers.BooleanField(read_only=True)
    can_report = serializers.SerializerMethodField()

    @property
    def moderating(self):
        return self.context.get("moderation", False)

    def is_author(self, obj):
        return obj.author_id == self.context["request"].user.pk

    def get_can_report(self, obj):
        viewer = self.context["request"].user
        if viewer.is_anonymous:
            return False
        protected = is_moderator(viewer) and outranks(obj.author, viewer)
        return not self.moderating and not self.is_author(obj) and not protected


class AudienceSerializerMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["groups"].child_relation.queryset = ContactGroup.objects.filter(
            owner=self.context["request"].user
        )

    def clean_audience(self, data):
        if data.get("visibility") == Post.Visibility.GLOBAL and not is_admin(
            self.context["request"].user
        ):
            raise serializers.ValidationError({"visibility": "Nur Admins können global posten."})
        if data.get("visibility") == Post.Visibility.GROUPS:
            if not data.get("groups"):
                raise serializers.ValidationError({"groups": "Wähle mindestens eine Gruppe."})
        else:
            data["groups"] = []
        return data


class OwnedNameSerializerMixin:
    def validate_name(self, name):
        name = name.strip()
        owned = self.Meta.model.objects.filter(owner=self.context["request"].user, name=name)
        if self.instance:
            owned = owned.exclude(pk=self.instance.pk)
        if owned.exists():
            raise serializers.ValidationError("Dieser Name ist schon vergeben.")
        return name


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
        aspect_ratio = serializers.FloatField(read_only=True)
        list_aspect_ratio = serializers.FloatField(read_only=True)
        like_count = CompactNumberField()
        comment_count = serializers.IntegerField(read_only=True)
        liked = serializers.BooleanField(read_only=True)
        reposted = serializers.BooleanField(read_only=True)
        reposter = serializers.CharField(read_only=True)
        saved = serializers.BooleanField(read_only=True)
        saved_folder = serializers.IntegerField(read_only=True)
        is_own = serializers.SerializerMethodField()

        class Meta(UUIDModelSerializer.read.Meta):
            model = Post
            fields = UUIDModelSerializer.read.Meta.fields + [
                "author",
                "text",
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

        def get_is_own(self, obj):
            return self.is_author(obj)

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
                raise serializers.ValidationError(str(error))

        def validate_video(self, upload):
            try:
                return videos.validate(upload)
            except videos.InvalidVideo as error:
                raise serializers.ValidationError(str(error))

        def validate(self, data):
            if data.get("images") and data.get("video"):
                raise serializers.ValidationError(
                    {"video": "Wähle entweder Bilder oder ein Video."}
                )
            if (
                not data.get("text", "").strip()
                and not data.get("images")
                and not data.get("video")
            ):
                raise serializers.ValidationError(
                    {"text": "Schreib etwas oder wähle ein Bild oder Video."}
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


class StoryModelSerializer(UUIDModelSerializer):
    class read(UUIDModelSerializer.read):
        image = serializers.CharField(source="image_url", read_only=True)
        expires_at = serializers.DateTimeField(read_only=True)
        is_own = serializers.SerializerMethodField()
        liked = serializers.BooleanField(read_only=True)
        like_count = serializers.SerializerMethodField()
        view_count = serializers.SerializerMethodField()
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

        def get_is_own(self, obj):
            return obj.author_id == self.context["request"].user.pk

        def get_like_count(self, obj):
            return compact_number(obj.like_total) if self.get_is_own(obj) else None

        def get_view_count(self, obj):
            return compact_number(obj.view_total) if self.get_is_own(obj) else None

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
                    {"visibility": "Stories können nicht global sein."}
                )
            return self.clean_audience(data)

        def create(self, data):
            return super().create({**data, "author": self.context["request"].user})


class HashtagModelSerializer(BaseModelSerializer):
    class read(BaseModelSerializer.read):
        post_count = CompactNumberField()
        following = serializers.BooleanField(read_only=True)

        class Meta(BaseModelSerializer.read.Meta):
            model = Hashtag
            fields = ["name", "post_count", "following"]


class CommentModelSerializer(UUIDModelSerializer):
    class read(ModeratedSerializerMixin, UUIDModelSerializer.read):
        post_id = serializers.UUIDField(source="post.uuid", read_only=True)
        parent_id = serializers.UUIDField(source="parent_uuid", read_only=True)
        author = AuthorModelSerializer.read(read_only=True)
        reply_to = serializers.CharField(read_only=True)
        is_post_author = serializers.BooleanField(read_only=True)
        reply_count = serializers.IntegerField(read_only=True)
        score = CompactNumberField()
        my_vote = serializers.IntegerField(read_only=True)
        latest_reply = serializers.SerializerMethodField()
        can_delete = serializers.SerializerMethodField()
        can_vote = serializers.SerializerMethodField()

        class Meta(UUIDModelSerializer.read.Meta):
            model = Comment
            fields = UUIDModelSerializer.read.Meta.fields + [
                "post_id",
                "parent_id",
                "author",
                "text",
                "created_at",
                "reply_to",
                "is_post_author",
                "reply_count",
                "score",
                "my_vote",
                "latest_reply",
                "can_delete",
                "can_vote",
                "hidden",
                "reported",
                "can_report",
            ]

        def get_latest_reply(self, obj):
            if obj.latest_reply is None:
                return None
            return CommentModelSerializer.read(obj.latest_reply, context=self.context).data

        def get_can_delete(self, obj):
            return not self.moderating and self.is_author(obj)

        def get_can_vote(self, obj):
            return not self.moderating and not self.is_author(obj)

    class write(BaseModelSerializer.write):
        class Meta(BaseModelSerializer.write.Meta):
            model = Comment
            fields = ["text"]

    class vote(serializers.Serializer):
        value = serializers.JSONField()

        def validate_value(self, value):
            if value not in (*CommentVote.Value.values, 0):
                raise serializers.ValidationError("Ungültige Stimme.")
            return value


class SavedFolderModelSerializer(BaseModelSerializer):
    class read(BaseModelSerializer.read):
        class Meta(BaseModelSerializer.read.Meta):
            model = SavedFolder
            fields = ["id", "name"]

    class write(OwnedNameSerializerMixin, BaseModelSerializer.write):
        class Meta(BaseModelSerializer.write.Meta):
            model = SavedFolder
            fields = ["name"]


class ContactGroupModelSerializer(BaseModelSerializer):
    class read(BaseModelSerializer.read):
        members = serializers.SlugRelatedField(slug_field="username", many=True, read_only=True)

        class Meta(BaseModelSerializer.read.Meta):
            model = ContactGroup
            fields = ["id", "name", "members"]

    class write(OwnedNameSerializerMixin, BaseModelSerializer.write):
        members = serializers.SlugRelatedField(
            slug_field="username",
            many=True,
            queryset=User.objects.filter(is_active=True),
            error_messages={"does_not_exist": "Den Benutzer «{value}» gibt es nicht."},
        )

        class Meta(BaseModelSerializer.write.Meta):
            model = ContactGroup
            fields = ["name", "members"]

        def validate_members(self, members):
            if self.context["request"].user in members:
                raise serializers.ValidationError("Du kannst dich nicht selbst hinzufügen.")
            return members


class AlbumModelSerializer(UUIDModelSerializer):
    class read(UUIDModelSerializer.read):
        cover = serializers.SerializerMethodField()
        is_own = serializers.SerializerMethodField()

        class Meta(UUIDModelSerializer.read.Meta):
            model = Album
            fields = UUIDModelSerializer.read.Meta.fields + [
                "name",
                "cover",
                "created_at",
                "is_own",
            ]

        def get_cover(self, album):
            if album.cover is None:
                return None
            viewer = self.context["request"].user
            if not Post.objects.apply_acl(viewer).filter(pk=album.cover.post_id).exists():
                return None
            return album.cover.post.thumbnail_url

        def get_is_own(self, album):
            return album.owner_id == self.context["request"].user.pk

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
