from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.models import UserProfile
from accounts.roles import is_admin, is_moderator, outranks, role_badge
from main.numbers import compact_number
from social.models import Follow, Friendship

from . import hashtags, images, videos
from .models import Comment, ContactGroup, Hashtag, Post, PostImage, SavedFolder

User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "avatar", "role"]

    def get_avatar(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.avatar if profile else ""

    def get_role(self, obj):
        return role_badge(obj) if self.profile_visible(obj) else None

    def profile_visible(self, obj):
        viewer = self.context["request"].user
        if obj == viewer or is_admin(viewer):
            return True
        relations = self.context.setdefault("viewer_relations", viewer_relations(viewer))
        visibility = getattr(getattr(obj, "profile", None), "profile_visibility", None)
        Visibility = UserProfile.Visibility
        return (
            visibility in (None, Visibility.PUBLIC)
            or (visibility == Visibility.FOLLOWERS and obj.pk in relations["following"])
            or obj.pk in relations["friends"]
        )


def viewer_relations(viewer):
    return {
        "following": set(
            Follow.objects.filter(follower=viewer).values_list("following_id", flat=True)
        ),
        "friends": set(Friendship.objects.filter(user=viewer).values_list("friend_id", flat=True)),
    }


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
