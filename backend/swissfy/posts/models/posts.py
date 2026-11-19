from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import (
    CharField,
    Count,
    Exists,
    F,
    IntegerField,
    OuterRef,
    Prefetch,
    Q,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from commons.models import BaseModel, BaseQuerySet, EncryptedTextField, boolean, count_of
from swissfy.accounts.roles import is_admin, is_moderator
from swissfy.moderation.models import Report, Warning

from .audience import (
    NAME_LENGTH,
    NOT_HIDDEN,
    TEXT_LENGTH,
    Audience,
    AudienceQuerySet,
    ContactGroup,
    HideableModel,
    ModeratedQuerySet,
    by_suspended_author,
    followed_by,
    reportable_by,
    shared_with_viewer,
)
from .feed import FeedEntry, Repost
from .saved import SavedPost
from .stories import Story, authors_for

POSTS_PER_DAY = 10


def aspect_ratio(width, height):
    return round(width / height, 4) if width and height else None


def unfinished_video():
    return Q(video_status__in=[Post.VideoStatus.PROCESSING, Post.VideoStatus.FAILED])


def reported_comments():
    return Q(pk__in=Comment.objects.filter(reports__isnull=False).values("pk"))


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


class PostQuerySet(ModeratedQuerySet, AudienceQuerySet):
    target_field = "post"

    def reported(self):
        reported = Q(reports__isnull=False) | Q(comments__reports__isnull=False)
        return self.filter(pk__in=Post.objects.filter(reported).values("pk"))

    def apply_acl(self, user, action="read"):
        if user.is_anonymous:
            return self.filter(
                NOT_HIDDEN & ~by_suspended_author() & ~unfinished_video(),
                visibility=Post.Visibility.GLOBAL,
                author__is_active=True,
            )
        groups = ContactGroup.objects.filter(posts=OuterRef("pk"))
        posts = self.with_audience(user, groups).filter(~unfinished_video() | Q(author=user))
        if is_admin(user):
            return posts
        shared = shared_with_viewer() | Q(visibility=Post.Visibility.GLOBAL)
        visible = NOT_HIDDEN & (Q(author=user) | (shared & ~by_suspended_author()))
        if is_moderator(user):
            visible |= Q(pk__in=Post.objects.filter(reports__isnull=False).values("pk"))
        return posts.filter(visible)

    def images(self):
        return self.exclude(thumbnail="").filter(video_status="")

    def videos(self):
        return self.filter(video_status=Post.VideoStatus.READY)

    def media(self):
        return self.exclude(thumbnail="").filter(video_status__in=["", Post.VideoStatus.READY])

    def by_media(self, images=False, videos=False, media=False):
        posts = self
        if images:
            posts = posts.images()
        if videos:
            posts = posts.videos()
        if media:
            posts = posts.media()
        return posts

    def feed(self, user):
        followed = followed_by(user)
        followed_hashtags = Post.objects.filter(hashtags__followers=user).values("pk")
        created = Q(feed_entries__repost=None) & (
            Q(author=user)
            | Q(author__in=followed)
            | Q(pk__in=followed_hashtags)
            | Q(visibility=Post.Visibility.GLOBAL)
        )
        reposted = Q(feed_entries__repost__user__in=followed)
        later_repost = Repost.objects.filter(
            post=OuterRef("pk"),
            user__in=followed,
            created_at__gt=OuterRef("feed_entries__shown_at"),
        )
        return (
            self.apply_acl(user)
            .filter((created | reposted) & ~Exists(later_repost))
            .annotate(shown_at=F("feed_entries__shown_at"), day=F("feed_entries__day"))
        )

    def backdate(self, created_at):
        entries = FeedEntry.objects.filter(post__in=self, repost=None)
        entries.update(shown_at=created_at, day=timezone.localdate(created_at))
        return self.update(created_at=created_at)

    def with_details(self, user):
        comments = Comment.objects.visible_to(user).filter(parent=None)
        posts = self.prefetch_related("groups", "images", authors_for(user)).annotate(
            like_count=count_of(Like.objects.all()), comment_count=count_of(comments)
        )
        if user.is_anonymous:
            return posts.annotate(
                is_own=Value(False),
                can_report=Value(False),
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
            is_own=boolean(Q(author=user)),
            can_report=reportable_by(user),
            reported=Exists(Report.objects.filter(post=OuterRef("pk"), reporter=user)),
            liked=Exists(Like.objects.filter(user=user, post=OuterRef("pk"))),
            reposted=Exists(Repost.objects.filter(user=user, post=OuterRef("pk"))),
            reposter=Subquery(reposter.values("user__username")[:1]),
            saved=Exists(saves),
            saved_folder=Subquery(saves.values("folder")),
        )


class Post(HideableModel):
    Visibility = Audience

    class VideoStatus(models.TextChoices):
        PROCESSING = "processing", _("Processing")
        READY = "ready", _("Ready")
        FAILED = "failed", _("Failed")

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

    def report_by(self, user):
        return Report.objects.get_or_create(reporter=user, post=self)

    def new_warning(self, moderator, reason):
        return Warning(user_id=self.author_id, moderator=moderator, reason=reason, post=self)

    @property
    def aspect_ratio(self):
        return aspect_ratio(self.image_width, self.image_height)

    @property
    def list_aspect_ratio(self):
        return max(self.aspect_ratio, 1) if self.aspect_ratio else None

    @property
    def thumbnail_url(self):
        if not self.thumbnail:
            return None
        return reverse("post-media-thumbnail", kwargs={"uuid": self.uuid})

    @property
    def has_video(self):
        return self.video_status == Post.VideoStatus.READY

    @property
    def video_url(self):
        if not self.has_video:
            return None
        return reverse("post-media-video", kwargs={"uuid": self.uuid})


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
        return reverse(
            "post-media-image", kwargs={"uuid": self.post.uuid, "position": self.position}
        )

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


def with_profile_media(members, viewer):
    posts = Post.objects.apply_acl(viewer).filter(author=OuterRef("pk"))
    stories = Story.objects.apply_acl(viewer).with_details(viewer).order_by("created_at")
    return members.annotate(
        has_pictures=Exists(posts.images()),
        has_reels=Exists(posts.videos()),
    ).prefetch_related(Prefetch("stories", queryset=stories, to_attr="visible_stories"))


class CommentQuerySet(ModeratedQuerySet):
    target_field = "comment"

    def visible_to(self, user):
        if user.is_anonymous:
            return self.filter(NOT_HIDDEN & ~by_suspended_author())
        if is_admin(user):
            return self.all()
        visible = NOT_HIDDEN & (~by_suspended_author() | Q(author=user))
        return self.filter(visible | reported_comments() if is_moderator(user) else visible)

    def parent_ids(self):
        return self.filter(parent__isnull=False).order_by("pk").values_list("pk", "parent_id")

    def on_reported_posts(self):
        return self.filter(post__in=Post.objects.reported())

    def apply_acl(self, user, action="read"):
        on_visible_post = Q(post__in=Post.objects.apply_acl(user)) | Q(author=user)
        return self.visible_to(user).filter(on_visible_post)

    def with_details(self, user):
        votes = CommentVote.objects.filter(comment=OuterRef("pk"))
        score = votes.order_by().values("comment").annotate(score=Sum("value")).values("score")
        reports = Report.objects.filter(comment=OuterRef("pk"), reporter=user)
        return (
            self.select_related("post", "parent__author")
            .prefetch_related(authors_for(user))
            .annotate(
                is_own=boolean(Q(author=user)),
                can_vote=boolean(~Q(author=user)),
                can_report=reportable_by(user),
                reported=Exists(reports),
                reply_count=count_of(Comment.objects.visible_to(user), "parent"),
                score=Coalesce(Subquery(score, output_field=IntegerField()), Value(0)),
                my_vote=Coalesce(Subquery(votes.filter(user=user).values("value")), Value(0)),
            )
        )


class Comment(HideableModel):
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

    def report_by(self, user):
        return Report.objects.get_or_create(reporter=user, comment=self)

    def new_warning(self, moderator, reason):
        return Warning(user_id=self.author_id, moderator=moderator, reason=reason, comment=self)

    def hide(self):
        thread = {self.pk}
        for pk, parent_id in Comment.objects.filter(post=self.post_id, pk__gt=self.pk).parent_ids():
            if parent_id in thread:
                thread.add(pk)
        visible = Comment.objects.filter(pk__in=thread).filter(NOT_HIDDEN | Q(pk=self.pk))
        visible.update(hidden_at=timezone.now())

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
        parents = dict(Comment.objects.filter(post=self.post_id, pk__lt=self.pk).parent_ids())
        ids = []
        parent_id = self.parent_id
        while parent_id:
            ids.insert(0, parent_id)
            parent_id = parents.get(parent_id)
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
