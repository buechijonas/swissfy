from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.models import UserProfile
from accounts.roles import is_admin, is_moderator, outranks, role_badge
from main.numbers import compact_number
from social.pictures import PictureField, cached_relations

from . import hashtags, images, videos
from .models import (
    STORY_LIFETIME,
    Album,
    AlbumEntry,
    Comment,
    ContactGroup,
    Hashtag,
    Post,
    PostImage,
    SavedFolder,
    Story,
)
from .queries import media_posts, visible_posts, visible_stories

User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    picture = PictureField()
    role = serializers.SerializerMethodField()
    has_story = serializers.SerializerMethodField()
    story_seen = serializers.SerializerMethodField()

    class Meta:
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

    def get_avatar(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.avatar if profile else ""

    def get_role(self, obj):
        return role_badge(obj) if self.profile_visible(obj) else None

    def story_authors(self):
        if "story_authors" not in self.context:
            viewer = self.context["request"].user
            stories = visible_stories(viewer)
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
        visibility = getattr(getattr(obj, "profile", None), "profile_visibility", None)
        Visibility = UserProfile.Visibility
        return (
            visibility in (None, Visibility.PUBLIC)
            or (visibility == Visibility.FOLLOWERS and obj.pk in relations["following"])
            or obj.pk in relations["friends"]
        )


class ModeratedMixin(serializers.Serializer):
    hidden = serializers.SerializerMethodField()
    reported = serializers.SerializerMethodField()
    can_report = serializers.SerializerMethodField()

    @property
    def moderating(self):
        return self.context.get("moderation", False)

    def is_author(self, obj):
        return obj.author_id == self.context["request"].user.pk

    def get_hidden(self, obj):
        return obj.hidden_at is not None

    def get_reported(self, obj):
        return getattr(obj, "reported", False)

    def get_can_report(self, obj):
        viewer = self.context["request"].user
        protected = is_moderator(viewer) and outranks(obj.author, viewer)
        return not self.moderating and not self.is_author(obj) and not protected


def thumbnail_url(post):
    return f"/api/posts/{post.uuid}/thumbnail/" if post.thumbnail else None


class PostSummarySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="uuid", read_only=True)
    author = AuthorSerializer(read_only=True)
    thumbnail = serializers.SerializerMethodField()
    comment_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = ["id", "author", "text", "thumbnail", "created_at", "comment_count"]

    def get_thumbnail(self, obj):
        return thumbnail_url(obj)


class PostSerializer(ModeratedMixin, serializers.ModelSerializer):
    id = serializers.UUIDField(source="uuid", read_only=True)
    author = AuthorSerializer(read_only=True)
    images = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    aspect_ratio = serializers.SerializerMethodField()
    list_aspect_ratio = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.IntegerField(read_only=True)
    liked = serializers.BooleanField(read_only=True)
    reposted = serializers.BooleanField(read_only=True)
    reposter = serializers.CharField(read_only=True)
    saved = serializers.BooleanField(read_only=True)
    saved_folder = serializers.IntegerField(read_only=True)
    is_own = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
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

    def get_images(self, obj):
        return [f"/api/posts/{obj.uuid}/images/{image.position}/" for image in obj.images.all()]

    def get_video(self, obj):
        if obj.video_status != Post.VideoStatus.READY:
            return None
        return f"/api/posts/{obj.uuid}/video/"

    def get_thumbnail(self, obj):
        return thumbnail_url(obj)

    def get_aspect_ratio(self, obj):
        return round(obj.image_width / obj.image_height, 4) if obj.image_height else None

    def get_list_aspect_ratio(self, obj):
        ratio = self.get_aspect_ratio(obj)
        return max(ratio, 1) if ratio else None

    def get_like_count(self, obj):
        return compact_number(obj.like_count)

    def get_is_own(self, obj):
        return self.is_author(obj)

    def to_representation(self, obj):
        data = super().to_representation(obj)
        if not data["is_own"]:
            del data["visibility"]
            del data["groups"]
        return data


class AudienceMixin:
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


class PostAudienceSerializer(AudienceMixin, serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["visibility", "groups"]
        extra_kwargs = {"visibility": {"required": True}}

    def validate(self, data):
        return self.clean_audience(data)


class PostCreateSerializer(AudienceMixin, serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.FileField(), required=False, allow_empty=False, write_only=True
    )
    video = serializers.FileField(required=False, write_only=True)

    class Meta:
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
            raise serializers.ValidationError({"video": "Wähle entweder Bilder oder ein Video."})
        if not data.get("text", "").strip() and not data.get("images") and not data.get("video"):
            raise serializers.ValidationError(
                {"text": "Schreib etwas oder wähle ein Bild oder Video."}
            )
        return self.clean_audience(data)

    def create(self, data):
        files = []
        if "images" in data:
            files, data["thumbnail"], data["image_width"], data["image_height"] = data.pop("images")
        if "video" in data:
            data["video_upload"] = data.pop("video")
            data["video_status"] = Post.VideoStatus.PROCESSING
        post = super().create({**data, "author": self.context["request"].user})
        hashtags.tag(post)
        PostImage.objects.bulk_create(
            PostImage(post=post, file=file, position=position)
            for position, file in enumerate(files)
        )
        return post


class StorySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="uuid", read_only=True)
    image = serializers.SerializerMethodField()
    expires_at = serializers.SerializerMethodField()
    is_own = serializers.SerializerMethodField()
    liked = serializers.BooleanField(read_only=True)
    like_count = serializers.SerializerMethodField()
    view_count = serializers.SerializerMethodField()
    seen = serializers.BooleanField(read_only=True)

    class Meta:
        model = Story
        fields = [
            "id",
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

    def get_image(self, obj):
        return f"/api/stories/{obj.uuid}/image/"

    def get_expires_at(self, obj):
        return obj.created_at + STORY_LIFETIME

    def get_is_own(self, obj):
        return obj.author_id == self.context["request"].user.pk

    def get_like_count(self, obj):
        return compact_number(obj.like_total) if self.get_is_own(obj) else None

    def get_view_count(self, obj):
        return compact_number(obj.view_total) if self.get_is_own(obj) else None


class StoryCreateSerializer(AudienceMixin, serializers.ModelSerializer):
    image = serializers.FileField(write_only=True)

    class Meta:
        model = Story
        fields = ["image", "text", "visibility", "groups"]

    def validate_image(self, upload):
        try:
            files, *_ = images.compress([upload])
        except images.InvalidImage as error:
            raise serializers.ValidationError(str(error))
        return files[0]

    def validate(self, data):
        if data.get("visibility") == Post.Visibility.GLOBAL:
            raise serializers.ValidationError({"visibility": "Stories können nicht global sein."})
        return self.clean_audience(data)

    def create(self, data):
        return super().create({**data, "author": self.context["request"].user})


class HashtagSerializer(serializers.ModelSerializer):
    post_count = serializers.SerializerMethodField()
    following = serializers.BooleanField(read_only=True)

    class Meta:
        model = Hashtag
        fields = ["name", "post_count", "following"]

    def get_post_count(self, obj):
        return compact_number(obj.post_count)


class CommentSerializer(ModeratedMixin, serializers.ModelSerializer):
    id = serializers.UUIDField(source="uuid", read_only=True)
    post_id = serializers.UUIDField(source="post.uuid", read_only=True)
    parent_id = serializers.SerializerMethodField()
    author = AuthorSerializer(read_only=True)
    reply_to = serializers.SerializerMethodField()
    is_post_author = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    my_vote = serializers.SerializerMethodField()
    latest_reply = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    can_vote = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
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

    def get_parent_id(self, obj):
        return obj.parent.uuid if obj.parent else None

    def get_reply_to(self, obj):
        return obj.parent.author.username if obj.parent else None

    def get_is_post_author(self, obj):
        return obj.author_id == obj.post.author_id

    def get_reply_count(self, obj):
        return getattr(obj, "reply_count", 0)

    def get_score(self, obj):
        return compact_number(getattr(obj, "score", 0))

    def get_my_vote(self, obj):
        return getattr(obj, "my_vote", 0)

    def get_latest_reply(self, obj):
        reply = getattr(obj, "latest_reply", None)
        return CommentSerializer(reply, context=self.context).data if reply else None

    def get_can_delete(self, obj):
        return not self.moderating and self.is_author(obj)

    def get_can_vote(self, obj):
        return not self.moderating and not self.is_author(obj)


class OwnedNameMixin:
    def validate_name(self, name):
        name = name.strip()
        owned = self.Meta.model.objects.filter(owner=self.context["request"].user, name=name)
        if self.instance:
            owned = owned.exclude(pk=self.instance.pk)
        if owned.exists():
            raise serializers.ValidationError("Dieser Name ist schon vergeben.")
        return name


class SavedFolderSerializer(OwnedNameMixin, serializers.ModelSerializer):
    class Meta:
        model = SavedFolder
        fields = ["id", "name"]


class ContactGroupSerializer(OwnedNameMixin, serializers.ModelSerializer):
    members = serializers.SlugRelatedField(
        slug_field="username",
        many=True,
        queryset=User.objects.filter(is_active=True),
        error_messages={"does_not_exist": "Den Benutzer «{value}» gibt es nicht."},
    )

    class Meta:
        model = ContactGroup
        fields = ["id", "name", "members"]

    def validate_members(self, members):
        if self.context["request"].user in members:
            raise serializers.ValidationError("Du kannst dich nicht selbst hinzufügen.")
        return members


class AlbumSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="uuid", read_only=True)
    cover = serializers.SlugRelatedField(
        slug_field="uuid", queryset=AlbumEntry.objects.none(), required=False, allow_null=True
    )

    class Meta:
        model = Album
        fields = ["id", "name", "cover", "created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(self.instance, Album):
            self.fields["cover"].queryset = self.instance.entries.all()

    def to_representation(self, album):
        data = super().to_representation(album)
        data["cover"] = self.cover_url(album.cover)
        data["is_own"] = album.owner_id == self.context["request"].user.pk
        return data

    def cover_url(self, entry):
        if entry is None:
            return None
        viewer = self.context["request"].user
        if not visible_posts(viewer).filter(pk=entry.post_id).exists():
            return None
        return thumbnail_url(entry.post)


class AlbumPostSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="uuid", read_only=True)
    author = AuthorSerializer(read_only=True)
    thumbnail = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ["id", "author", "thumbnail", "video"]

    def get_thumbnail(self, obj):
        return thumbnail_url(obj)

    def get_video(self, obj):
        return obj.video_status == Post.VideoStatus.READY


class AlbumEntrySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="uuid", read_only=True)
    post = serializers.SlugRelatedField(slug_field="uuid", queryset=Post.objects.none())

    class Meta:
        model = AlbumEntry
        fields = ["id", "post", "date", "title"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.context["request"].user
        self.fields["post"].queryset = media_posts(Post.objects.filter(author=user))

    def to_representation(self, entry):
        data = super().to_representation(entry)
        data["post"] = AlbumPostSerializer(entry.post, context=self.context).data
        return data
