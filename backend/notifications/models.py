from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from moderation.models import Suspension, Warning
from posts.models import Comment, Post


class Notification(models.Model):
    class Resolution(models.TextChoices):
        ACCEPTED = "accepted", "Angenommen"
        DECLINED = "declined", "Abgelehnt"

    class Kind(models.TextChoices):
        WARNING = "warning", "Verwarnung"
        WARNING_EXPIRED = "warning_expired", "Verwarnung verjährt"
        SUSPENSION = "suspension", "Kontosperre"
        COMMENT = "comment", "Kommentar"
        LIKE = "like", "Gefällt mir"
        FOLLOW = "follow", "Neuer Follower"
        FOLLOW_REQUEST = "follow_request", "Followeranfrage"
        FRIEND_REQUEST = "friend_request", "Freundschaftsanfrage"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="+"
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    warning = models.ForeignKey(Warning, on_delete=models.CASCADE, null=True, blank=True)
    suspension = models.ForeignKey(Suspension, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)
    resolution = models.CharField(max_length=10, choices=Resolution.choices, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["recipient", "-created_at"], name="notification_inbox"),
            models.Index(
                fields=["recipient"], condition=Q(read_at__isnull=True), name="notification_unread"
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["warning"],
                condition=Q(kind="warning_expired"),
                name="one_expiry_notification_per_warning",
            ),
        ]
