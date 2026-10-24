from datetime import timedelta
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone

TEXT_LENGTH = 500
NAME_LENGTH = 50
STORY_TEXT_LENGTH = 200
STORY_LIFETIME = timedelta(hours=24)


class ContactGroup(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contact_groups"
    )
    name = models.CharField(max_length=NAME_LENGTH)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="+", blank=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "name"], name="unique_contact_group"),
        ]

    def __str__(self):
        return f"{self.owner}: {self.name}"


class Hashtag(models.Model):
    name = models.CharField(max_length=NAME_LENGTH, unique=True)
    followers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="followed_hashtags", blank=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"#{self.name}"


class Post(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = "public", "Alle"
        FOLLOWERS = "followers", "Follower"
        FRIENDS = "friends", "Freunde"
        GROUPS = "groups", "Gruppen"
        GLOBAL = "global", "Global"

    class VideoStatus(models.TextChoices):
        PROCESSING = "processing", "Wird verarbeitet"
        READY = "ready", "Bereit"
        FAILED = "failed", "Fehlgeschlagen"

    uuid = models.UUIDField(default=uuid4, unique=True, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    text = models.TextField(max_length=TEXT_LENGTH, blank=True)
    thumbnail = models.FileField(upload_to="posts/thumbnails/", blank=True)
    image_width = models.PositiveIntegerField(null=True, blank=True)
    image_height = models.PositiveIntegerField(null=True, blank=True)
    video = models.FileField(upload_to="posts/videos/", blank=True)
    video_upload = models.FileField(upload_to="posts/uploads/", blank=True)
    video_status = models.CharField(
        max_length=20, choices=VideoStatus.choices, blank=True, db_index=True
    )
    visibility = models.CharField(
        max_length=20, choices=Visibility.choices, default=Visibility.PUBLIC
    )
    groups = models.ManyToManyField(ContactGroup, related_name="posts", blank=True)
    hashtags = models.ManyToManyField(Hashtag, related_name="posts", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    hidden_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Post({self.author}, {self.pk})"


class PostCreation(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    file = models.FileField(upload_to="posts/")
    position = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["post", "position"], name="unique_post_image"),
        ]


@receiver(post_delete, sender=Post)
def delete_post_files(sender, instance, **kwargs):
    instance.thumbnail.delete(save=False)
    instance.video.delete(save=False)
    instance.video_upload.delete(save=False)


@receiver(post_delete, sender=PostImage)
def delete_post_image(sender, instance, **kwargs):
    instance.file.delete(save=False)


class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "post"], name="unique_like")]


class Story(models.Model):
    uuid = models.UUIDField(default=uuid4, unique=True, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="stories"
    )
    image = models.FileField(upload_to="stories/")
    text = models.CharField(max_length=STORY_TEXT_LENGTH, blank=True)
    visibility = models.CharField(
        max_length=20, choices=Post.Visibility.choices, default=Post.Visibility.PUBLIC
    )
    groups = models.ManyToManyField(ContactGroup, related_name="stories", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"Story({self.author}, {self.pk})"


def story_cutoff():
    return timezone.now() - STORY_LIFETIME


class StoryLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "story"], name="unique_story_like")]


class StoryView(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="views")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "story"], name="unique_story_view")]


@receiver(post_delete, sender=Story)
def delete_story_image(sender, instance, **kwargs):
    instance.image.delete(save=False)


class Repost(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reposts")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "post"], name="unique_repost")]


class Comment(models.Model):
    uuid = models.UUIDField(default=uuid4, unique=True, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    text = models.TextField(max_length=TEXT_LENGTH)
    created_at = models.DateTimeField(auto_now_add=True)
    hidden_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["post", "parent", "created_at"], name="comment_thread")]

    def __str__(self):
        return f"Comment({self.author}, {self.post_id})"


class CommentVote(models.Model):
    class Value(models.IntegerChoices):
        UP = 1
        DOWN = -1

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="votes")
    value = models.SmallIntegerField(choices=Value.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "comment"], name="unique_comment_vote"),
        ]


class SavedFolder(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_folders"
    )
    name = models.CharField(max_length=NAME_LENGTH)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "name"], name="unique_saved_folder"),
        ]

    def __str__(self):
        return f"{self.owner}: {self.name}"


class SavedPost(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_posts"
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="saves")
    folder = models.ForeignKey(
        SavedFolder, on_delete=models.SET_NULL, null=True, blank=True, related_name="saved_posts"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "post"], name="unique_saved_post"),
        ]


class Album(models.Model):
    uuid = models.UUIDField(default=uuid4, unique=True, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="albums"
    )
    name = models.CharField(max_length=NAME_LENGTH)
    cover = models.ForeignKey(
        "AlbumEntry", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "-created_at", "-id"]

    def __str__(self):
        return self.name


class AlbumEntry(models.Model):
    uuid = models.UUIDField(default=uuid4, unique=True, editable=False)
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="entries")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="+")
    date = models.DateField(null=True, blank=True)
    title = models.CharField(max_length=NAME_LENGTH, blank=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(fields=["album", "post"], name="unique_album_post"),
        ]
