from django.conf import settings
from django.db import models
from django.db.models import Min, Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from commons.models import BaseModel, BaseQuerySet

from .audience import followed_by


class RepostQuerySet(BaseQuerySet):
    def followed_by(self, user):
        return self.filter(user__in=followed_by(user)).order_by("-created_at")


class Repost(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    post = models.ForeignKey("posts.Post", on_delete=models.CASCADE, related_name="reposts")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = RepostQuerySet.as_manager()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "post"], name="unique_repost")]
        indexes = [models.Index(fields=["post", "-created_at"], name="repost_latest")]


class FeedEntryQuerySet(BaseQuerySet):
    def oldest_day(self):
        return self.aggregate(oldest=Min("day"))["oldest"]


class FeedEntry(BaseModel):
    post = models.ForeignKey("posts.Post", on_delete=models.CASCADE, related_name="feed_entries")
    repost = models.OneToOneField(
        Repost, on_delete=models.CASCADE, null=True, blank=True, related_name="feed_entry"
    )
    shown_at = models.DateTimeField()
    day = models.DateField()

    objects = FeedEntryQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post"], condition=Q(repost=None), name="unique_post_feed_entry"
            ),
        ]
        indexes = [models.Index(fields=["-day", "-shown_at"], name="feed_entry_order")]

    @classmethod
    def record(cls, post, shown_at, repost=None):
        return cls.objects.create(
            post=post, repost=repost, shown_at=shown_at, day=timezone.localdate(shown_at)
        )


@receiver(post_save, sender="posts.Post")
def add_post_feed_entry(sender, instance, created, **kwargs):
    if created:
        FeedEntry.record(instance, instance.created_at)


@receiver(post_save, sender=Repost)
def add_repost_feed_entry(sender, instance, created, **kwargs):
    if created:
        FeedEntry.record(instance.post, instance.created_at, instance)
