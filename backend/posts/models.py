from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import (
    CharField,
    Count,
    Exists,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce, Greatest, TruncDate
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone

from accounts.models import UserProfile
from accounts.roles import is_admin, is_moderator
from commons.models import BaseModel, BaseQuerySet, EncryptedTextField, UUIDModel
from moderation.sanctions import is_suspended, suspended_users
from social.models import Follow, Friendship

TEXT_LENGTH = 500
NAME_LENGTH = 50
STORY_TEXT_LENGTH = 200
STORY_LIFETIME = timedelta(hours=24)
POSTS_PER_DAY = 10

NOT_HIDDEN = Q(hidden_at__isnull=True)


def story_cutoff():
    return timezone.now() - STORY_LIFETIME


def aspect_ratio(width, height):
    return round(width / height, 4) if width and height else None


def count_of(queryset, field="post"):
    counts = (
        queryset.filter(**{field: OuterRef("pk")})
        .order_by()
        .values(field)
        .annotate(count=Count("pk"))
        .values("count")
    )
    return Coalesce(Subquery(counts, output_field=IntegerField()), Value(0))


def unfinished_video():
    return Q(video_status__in=[Post.VideoStatus.PROCESSING, Post.VideoStatus.FAILED])


def reported_comments():
    return Q(pk__in=Comment.objects.filter(reports__isnull=False).values("pk"))


def by_suspended_author():
    return Q(author__in=suspended_users())


def followed_by(user):
    followed = Follow.objects.filter(follower=user).values("following")
    friends = Friendship.objects.filter(user=user).values("friend")
    return followed.union(friends)


class AudienceQuerySet(BaseQuerySet):
    def with_audience(self, user, groups):
        Audience = Post.Visibility
        Profile = UserProfile.Visibility
        profile_visible = (
            Q(author__profile__profile_visibility=Profile.PUBLIC)
            | Q(author__profile__profile_visibility=Profile.FOLLOWERS, viewer_follows=True)
            | Q(viewer_is_friend=True)
        )
        audience = (
            Q(visibility=Audience.PUBLIC)
            | Q(visibility=Audience.FOLLOWERS, viewer_follows=True)
            | Q(visibility=Audience.FRIENDS, viewer_is_friend=True)
            | Q(visibility=Audience.GROUPS, viewer_in_group=True)
        )
        items = self.filter(author__is_active=True).annotate(
            viewer_follows=Exists(
                Follow.objects.filter(follower=user, following=OuterRef("author"))
            ),
            viewer_is_friend=Exists(
                Friendship.objects.filter(user=user, friend=OuterRef("author"))
            ),
            viewer_in_group=Exists(groups.filter(members=user)),
        )
        return items, profile_visible & audience


class ContactGroup(BaseModel):
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


class HashtagQuerySet(BaseQuerySet):
    def with_stats(self, user):
        followers = Hashtag.followers.through.objects.filter(hashtag=OuterRef("pk"), user=user)
        visible = Post.objects.apply_acl(user).values("pk")
        return self.annotate(
            post_count=Count("posts", filter=Q(posts__in=visible), distinct=True),
            following=Exists(followers),
        )


class Hashtag(BaseModel):
    name = models.CharField(max_length=NAME_LENGTH, unique=True)
    followers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="followed_hashtags", blank=True
    )

    objects = HashtagQuerySet.as_manager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"#{self.name}"


class HideableModel(UUIDModel):
    label = None

    hidden_at = models.DateTimeField(null=True, blank=True)

    class Meta(UUIDModel.Meta):
        abstract = True

    @property
    def is_hidden(self):
        return self.hidden_at is not None

    @property
    def unavailable(self):
        if self.hidden_at:
            reason = f"Dieser {self.label} wurde gesperrt."
        elif is_suspended(self.author):
            reason = "Der User wurde gesperrt und ist nicht sichtbar."
        else:
            reason = f"Dieser {self.label} ist nicht sichtbar."
        return {"id": str(self.uuid), "unavailable": reason}


class PostQuerySet(AudienceQuerySet):
    def apply_acl(self, user):
        if user.is_anonymous:
            return self.filter(
                NOT_HIDDEN & ~by_suspended_author() & ~unfinished_video(),
                visibility=Post.Visibility.GLOBAL,
                author__is_active=True,
            )
        posts, shared = self.with_audience(user, ContactGroup.objects.filter(posts=OuterRef("pk")))
        posts = posts.filter(~unfinished_video() | Q(author=user))
        if is_admin(user):
            return posts
        global_post = Q(visibility=Post.Visibility.GLOBAL)
        visible = NOT_HIDDEN & (Q(author=user) | ((shared | global_post) & ~by_suspended_author()))
        if is_moderator(user):
            visible |= Q(pk__in=Post.objects.filter(reports__isnull=False).values("pk"))
        return posts.filter(visible)

    def images(self):
        return self.exclude(thumbnail="").filter(video_status="")

    def videos(self):
        return self.filter(video_status=Post.VideoStatus.READY)

    def media(self):
        return self.exclude(thumbnail="").filter(video_status__in=["", Post.VideoStatus.READY])

    def by_media(self, params):
        posts = self
        if params.get("images"):
            posts = posts.images()
        if params.get("videos"):
            posts = posts.videos()
        if params.get("media"):
            posts = posts.media()
        return posts

    def feed(self, user):
        reposts = Repost.objects.followed_by(user)
        reposted_at = Subquery(reposts.filter(post=OuterRef("pk")).values("created_at")[:1])
        followed_hashtags = Post.objects.filter(hashtags__followers=user).values("pk")
        return (
            self.apply_acl(user)
            .filter(
                Q(author=user)
                | Q(author__in=followed_by(user))
                | Q(pk__in=followed_hashtags)
                | Q(visibility=Post.Visibility.GLOBAL)
                | Q(pk__in=reposts.values("post"))
            )
            .annotate(shown_at=Greatest("created_at", Coalesce(reposted_at, "created_at")))
            .annotate(day=TruncDate("shown_at"))
        )

    def with_details(self, user):
        comments = Comment.objects.visible_to(user).filter(parent=None)
        posts = (
            self.select_related("author__profile")
            .prefetch_related("groups", "images", "author__groups")
            .annotate(like_count=count_of(Like.objects.all()), comment_count=count_of(comments))
        )
        if user.is_anonymous:
            return posts.annotate(
                reported=Value(False),
                liked=Value(False),
                reposted=Value(False),
                reposter=Value(None, output_field=CharField()),
                saved=Value(False),
                saved_folder=Value(None, output_field=IntegerField()),
            )
        saves = SavedPost.objects.filter(user=user, post=OuterRef("pk"))
        reposter = Repost.objects.followed_by(user).filter(post=OuterRef("pk"))
        return posts.annotate(
            reported=Exists(Post.objects.filter(pk=OuterRef("pk"), reports__reporter=user)),
            liked=Exists(Like.objects.filter(user=user, post=OuterRef("pk"))),
            reposted=Exists(Repost.objects.filter(user=user, post=OuterRef("pk"))),
            reposter=Subquery(reposter.values("user__username")[:1]),
            saved=Exists(saves),
            saved_folder=Subquery(saves.values("folder")),
        )


class Post(HideableModel):
    label = "Feed"

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

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    text = EncryptedTextField(max_length=TEXT_LENGTH, blank=True)
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

    objects = PostQuerySet.as_manager()

    def __str__(self):
        return f"Post({self.author}, {self.pk})"

    @property
    def aspect_ratio(self):
        return aspect_ratio(self.image_width, self.image_height)

    @property
    def list_aspect_ratio(self):
        return max(self.aspect_ratio, 1) if self.aspect_ratio else None

    @property
    def thumbnail_url(self):
        return f"/api/posts/{self.uuid}/thumbnail/" if self.thumbnail else None

    @property
    def has_video(self):
        return self.video_status == Post.VideoStatus.READY

    @property
    def video_url(self):
        return f"/api/posts/{self.uuid}/video/" if self.has_video else None


class PostCreationQuerySet(BaseQuerySet):
    def recent(self):
        return self.filter(created_at__gte=timezone.now() - timedelta(days=1))

    def stale(self):
        return self.filter(created_at__lt=timezone.now() - timedelta(days=1))

    def remaining(self, user):
        return max(0, POSTS_PER_DAY - self.filter(author=user).recent().count())


class PostCreation(BaseModel):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = PostCreationQuerySet.as_manager()


class PostImage(BaseModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    file = models.FileField(upload_to="posts/")
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    position = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["post", "position"], name="unique_post_image"),
        ]

    @property
    def url(self):
        return f"/api/posts/{self.post.uuid}/images/{self.position}/"

    @property
    def aspect_ratio(self):
        return aspect_ratio(self.width, self.height) or self.post.aspect_ratio


@receiver(post_delete, sender=Post)
def delete_post_files(sender, instance, **kwargs):
    instance.thumbnail.delete(save=False)
    instance.video.delete(save=False)
    instance.video_upload.delete(save=False)


@receiver(post_delete, sender=PostImage)
def delete_post_image(sender, instance, **kwargs):
    instance.file.delete(save=False)


class Like(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "post"], name="unique_like")]


class StoryQuerySet(AudienceQuerySet):
    def active(self):
        return self.filter(created_at__gte=story_cutoff())

    def apply_acl(self, user):
        groups = ContactGroup.objects.filter(stories=OuterRef("pk"))
        stories, shared = self.active().with_audience(user, groups)
        if is_admin(user):
            return stories
        return stories.filter(Q(author=user) | (shared & ~by_suspended_author()))

    def with_details(self, user):
        return self.annotate(
            liked=Exists(StoryLike.objects.filter(story=OuterRef("pk"), user=user)),
            seen=Exists(StoryView.objects.filter(story=OuterRef("pk"), user=user)),
            like_total=count_of(StoryLike.objects.all(), "story"),
            view_total=count_of(StoryView.objects.exclude(user=OuterRef("author")), "story"),
        )


class Story(UUIDModel):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="stories"
    )
    image = models.FileField(upload_to="stories/")
    text = EncryptedTextField(max_length=STORY_TEXT_LENGTH, blank=True)
    visibility = models.CharField(
        max_length=20, choices=Post.Visibility.choices, default=Post.Visibility.PUBLIC
    )
    groups = models.ManyToManyField(ContactGroup, related_name="stories", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = StoryQuerySet.as_manager()

    def __str__(self):
        return f"Story({self.author}, {self.pk})"

    @property
    def image_url(self):
        return f"/api/stories/{self.uuid}/image/"

    @property
    def expires_at(self):
        return self.created_at + STORY_LIFETIME


class StoryLike(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "story"], name="unique_story_like")]


class StoryView(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="views")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "story"], name="unique_story_view")]


@receiver(post_delete, sender=Story)
def delete_story_image(sender, instance, **kwargs):
    instance.image.delete(save=False)


class RepostQuerySet(BaseQuerySet):
    def followed_by(self, user):
        return self.filter(user__in=followed_by(user)).order_by("-created_at")


class Repost(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reposts")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = RepostQuerySet.as_manager()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "post"], name="unique_repost")]


class CommentQuerySet(BaseQuerySet):
    def visible_to(self, user):
        if user.is_anonymous:
            return self.filter(NOT_HIDDEN & ~by_suspended_author())
        if is_admin(user):
            return self.all()
        visible = NOT_HIDDEN & (~by_suspended_author() | Q(author=user))
        return self.filter(visible | reported_comments() if is_moderator(user) else visible)

    def apply_acl(self, user):
        on_visible_post = Q(post__in=Post.objects.apply_acl(user)) | Q(author=user)
        return self.visible_to(user).filter(on_visible_post)

    def with_details(self, user):
        votes = CommentVote.objects.filter(comment=OuterRef("pk"))
        score = votes.order_by().values("comment").annotate(score=Sum("value")).values("score")
        reports = Comment.objects.filter(pk=OuterRef("pk"), reports__reporter=user)
        return (
            self.select_related("post", "author__profile", "parent__author")
            .prefetch_related("author__groups")
            .annotate(
                reported=Exists(reports),
                reply_count=count_of(Comment.objects.visible_to(user), "parent"),
                score=Coalesce(Subquery(score, output_field=IntegerField()), Value(0)),
                my_vote=Coalesce(Subquery(votes.filter(user=user).values("value")), Value(0)),
            )
        )


class Comment(HideableModel):
    label = "Kommentar"
    latest_reply = None

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    text = EncryptedTextField(max_length=TEXT_LENGTH)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CommentQuerySet.as_manager()

    class Meta:
        indexes = [models.Index(fields=["post", "parent", "created_at"], name="comment_thread")]

    def __str__(self):
        return f"Comment({self.author}, {self.post_id})"

    @property
    def parent_uuid(self):
        return self.parent.uuid if self.parent else None

    @property
    def reply_to(self):
        return self.parent.author.username if self.parent else None

    @property
    def is_post_author(self):
        return self.author_id == self.post.author_id

    @property
    def ancestor_ids(self):
        ids = []
        parent_id = self.parent_id
        while parent_id:
            ids.insert(0, parent_id)
            parent_id = Comment.objects.values_list("parent_id", flat=True).get(pk=parent_id)
        return ids

    @staticmethod
    def attach_latest_replies(comments, replies):
        latest = replies.filter(parent__in=comments).order_by("parent", "-id").distinct("parent")
        by_parent = {reply.parent_id: reply for reply in latest}
        for comment in comments:
            comment.latest_reply = by_parent.get(comment.pk)
        return comments


class CommentVote(BaseModel):
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


class SavedFolder(BaseModel):
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


class SavedPostQuerySet(BaseQuerySet):
    def in_folder(self, folder):
        if not folder:
            return self
        if folder == "none":
            return self.filter(folder=None)
        return self.filter(folder=folder) if folder.isdigit() else self.none()


class SavedPost(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_posts"
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="saves")
    folder = models.ForeignKey(
        SavedFolder, on_delete=models.SET_NULL, null=True, blank=True, related_name="saved_posts"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = SavedPostQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "post"], name="unique_saved_post"),
        ]


class Album(UUIDModel):
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


class AlbumEntry(UUIDModel):
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
