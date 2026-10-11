from django.contrib.auth import get_user_model
from rest_framework import serializers

from main.numbers import compact_number

from . import images
from .models import Comment, ContactGroup, Post, PostImage, SavedFolder

User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "avatar"]

    def get_avatar(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.avatar if profile else ""


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


class PostSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="uuid", read_only=True)
    author = AuthorSerializer(read_only=True)
    images = serializers.SerializerMethodField()
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
        ]

    def get_images(self, obj):
        return [f"/api/posts/{obj.uuid}/images/{image.position}/" for image in obj.images.all()]

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
        return obj.author_id == self.context["request"].user.pk

    def to_representation(self, obj):
        data = super().to_representation(obj)
        if not data["is_own"]:
            del data["visibility"]
            del data["groups"]
        return data


class PostCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.FileField(), required=False, allow_empty=False, write_only=True
    )

    class Meta:
        model = Post
        fields = ["text", "images", "visibility", "groups"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["groups"].child_relation.queryset = ContactGroup.objects.filter(
            owner=self.context["request"].user
        )

    def validate_images(self, uploads):
        try:
            return images.compress(uploads)
        except images.InvalidImage as error:
            raise serializers.ValidationError(str(error))

    def validate(self, data):
        if not data.get("text", "").strip() and not data.get("images"):
            raise serializers.ValidationError({"text": "Schreib etwas oder wähle ein Bild."})
        if data.get("visibility") == Post.Visibility.GROUPS:
            if not data.get("groups"):
                raise serializers.ValidationError({"groups": "Wähle mindestens eine Gruppe."})
        else:
            data["groups"] = []
        return data

    def create(self, data):
        files = []
        if "images" in data:
            files, data["thumbnail"], data["image_width"], data["image_height"] = data.pop("images")
        post = super().create({**data, "author": self.context["request"].user})
        PostImage.objects.bulk_create(
            PostImage(post=post, file=file, position=position)
            for position, file in enumerate(files)
        )
        return post


class CommentSerializer(serializers.ModelSerializer):
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
        return obj.author_id == self.context["request"].user.pk

    def get_can_vote(self, obj):
        return not self.get_can_delete(obj)


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
