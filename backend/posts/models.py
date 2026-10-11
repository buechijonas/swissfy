from uuid import uuid4

from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

TEXT_LENGTH = 500
NAME_LENGTH = 50


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


class Post(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = "public", "Alle"
        FOLLOWERS = "followers", "Follower"
        FRIENDS = "friends", "Freunde"
        GROUPS = "groups", "Gruppen"

    uuid = models.UUIDField(default=uuid4, unique=True, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    text = models.TextField(max_length=TEXT_LENGTH, blank=True)
    thumbnail = models.FileField(upload_to="posts/thumbnails/", blank=True)
    image_width = models.PositiveIntegerField(null=True, blank=True)
    image_height = models.PositiveIntegerField(null=True, blank=True)
    visibility = models.CharField(
        max_length=20, choices=Visibility.choices, default=Visibility.PUBLIC
    )
    groups = models.ManyToManyField(ContactGroup, related_name="posts", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
def delete_post_thumbnail(sender, instance, **kwargs):
    instance.thumbnail.delete(save=False)


@receiver(post_delete, sender=PostImage)
def delete_post_image(sender, instance, **kwargs):
    instance.file.delete(save=False)


class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "post"], name="unique_like")]


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
