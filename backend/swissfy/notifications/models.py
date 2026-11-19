from django.conf import settings
from django.db import models
from django.db.models import Exists, OuterRef, Q
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from commons import events
from commons.i18n import local_date
from commons.models import BaseModel, BaseQuerySet
from swissfy.moderation.models import WARNING_EXPIRY, Suspension, Warning
from swissfy.posts.models import authors_for
from swissfy.social.models import Follow, FollowRequest, FriendRequest, Friendship

PREVIEW_LENGTH = 80
NOTIFICATION_EVENT = "notification"


def quote(text):
    text = " ".join(text.split())
    return f"«{text[:PREVIEW_LENGTH]}…»" if len(text) > PREVIEW_LENGTH else f"«{text}»"


class NotificationQuerySet(BaseQuerySet):
    def apply_acl(self, user, action="read"):
        if user.is_anonymous:
            return self.none()
        return self.filter(recipient=user)

    def unread(self):
        return self.filter(read_at=None)

    def with_details(self, user):
        actor, recipient = OuterRef("actor"), OuterRef("recipient")
        details = self.select_related("recipient", "post", "comment", "warning", "suspension")
        return details.prefetch_related(authors_for(user, "actor")).annotate(
            follow_pending=Exists(
                FollowRequest.objects.filter(follower=actor, following=recipient)
            ),
            follow_accepted=Exists(Follow.objects.filter(follower=actor, following=recipient)),
            friend_pending=Exists(FriendRequest.objects.filter(sender=actor, receiver=recipient)),
            friend_accepted=Exists(Friendship.objects.filter(user=recipient, friend=actor)),
        )

    def publish(self):
        recipients = self.order_by().values_list("recipient", flat=True).distinct()
        events.publish(recipients, NOTIFICATION_EVENT)

    def mark_read(self):
        unread = self.unread()
        unread.publish()
        return unread.update(read_at=timezone.now())

    def withdraw(self, recipient, kind, actor, **targets):
        return self.filter(recipient=recipient, kind=kind, actor=actor, **targets).delete()

    def resolve_request(self, recipient, kind, actor, resolution):
        requests = self.filter(recipient=recipient, actor=actor, kind=kind, resolution="")
        requests.publish()
        return requests.update(resolution=resolution)

    def sync_expired_warnings(self, user):
        now = timezone.now()
        notified = self.filter(warning=OuterRef("pk"), kind=Notification.Kind.WARNING_EXPIRED)
        expired = Warning.objects.filter(user=user, created_at__lte=now - WARNING_EXPIRY)
        return self.bulk_create(
            [
                Notification(
                    recipient=user,
                    kind=Notification.Kind.WARNING_EXPIRED,
                    warning=warning,
                    created_at=warning.created_at + WARNING_EXPIRY,
                )
                for warning in expired.exclude(Exists(notified))
            ],
            ignore_conflicts=True,
        )


class Notification(BaseModel):
    class Resolution(models.TextChoices):
        ACCEPTED = "accepted", _("Accepted")
        DECLINED = "declined", _("Declined")

    class Kind(models.TextChoices):
        WARNING = "warning", _("Warning")
        WARNING_EXPIRED = "warning_expired", _("Warning expired")
        SUSPENSION = "suspension", _("Suspension")
        COMMENT = "comment", _("Comment")
        LIKE = "like", _("Like")
        FOLLOW = "follow", _("New follower")
        FOLLOW_REQUEST = "follow_request", _("Follow request")
        FRIEND_REQUEST = "friend_request", _("Friend request")

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="+"
    )
    post = models.ForeignKey("posts.Post", on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey("posts.Comment", on_delete=models.CASCADE, null=True, blank=True)
    warning = models.ForeignKey(Warning, on_delete=models.CASCADE, null=True, blank=True)
    suspension = models.ForeignKey(Suspension, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)
    resolution = models.CharField(max_length=10, choices=Resolution.choices, blank=True)

    objects = NotificationQuerySet.as_manager()

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

    @classmethod
    def notify(cls, recipient, kind, actor=None, **targets):
        if actor is not None and actor.pk == recipient.pk:
            return None
        return cls.objects.create(recipient=recipient, kind=kind, actor=actor, **targets)

    @property
    def is_read(self):
        return self.read_at is not None

    @property
    def actor_name(self):
        return f"@{self.actor.username}" if self.actor else ""

    @property
    def message(self):
        Kind = self.Kind
        match self.kind:
            case Kind.WARNING:
                return _("You have been warned: %(reason)s.") % {
                    "reason": self.warning.get_reason_display()
                }
            case Kind.WARNING_EXPIRED:
                return _("Your warning “%(reason)s” from %(created)s has expired.") % {
                    "reason": self.warning.get_reason_display(),
                    "created": local_date(self.warning.created_at),
                }
            case Kind.SUSPENSION:
                return self.suspension_message
            case Kind.COMMENT:
                return _("%(actor)s commented on your feed: %(text)s") % {
                    "actor": self.actor_name,
                    "text": quote(self.comment.text),
                }
            case Kind.LIKE:
                return _("%(actor)s likes your feed.") % {"actor": self.actor_name}
            case Kind.FOLLOW:
                return _("%(actor)s is now following you.") % {"actor": self.actor_name}
            case Kind.FOLLOW_REQUEST:
                return _("%(actor)s wants to follow you.") % {"actor": self.actor_name}
            case Kind.FRIEND_REQUEST:
                return _("%(actor)s wants to be your friend.") % {"actor": self.actor_name}
        return ""

    @property
    def suspension_message(self):
        suspension = self.suspension
        if suspension.ends_at is None:
            return _("Your account has been suspended permanently.")
        dates = {
            "duration": suspension.duration_label,
            "start": local_date(suspension.starts_at),
            "until": local_date(suspension.ends_at),
        }
        if suspension.starts_at > timezone.now():
            return (
                _(
                    "Your account will be suspended for %(duration)s, "
                    "from %(start)s until %(until)s."
                )
                % dates
            )
        return _("Your account has been suspended for %(duration)s, until %(until)s.") % dates

    @property
    def link(self):
        Kind = self.Kind
        match self.kind:
            case Kind.WARNING | Kind.WARNING_EXPIRED | Kind.SUSPENSION:
                return f"/profile/{self.recipient.username}?tab=status"
            case Kind.COMMENT:
                return f"/comments/{self.comment.uuid}"
            case Kind.LIKE:
                return f"/posts/{self.post.uuid}"
        return f"/profile/{self.actor.username}" if self.actor else None

    @property
    def request_state(self):
        match self.kind:
            case self.Kind.FOLLOW_REQUEST:
                pending, accepted = self.follow_pending, self.follow_accepted
            case self.Kind.FRIEND_REQUEST:
                pending, accepted = self.friend_pending, self.friend_accepted
            case _:
                return None
        if self.resolution:
            return self.resolution
        if pending:
            return "pending"
        return self.Resolution.ACCEPTED if accepted else self.Resolution.DECLINED


@receiver([post_save, post_delete], sender=Notification)
def publish_notification(sender, instance, **kwargs):
    events.publish([instance.recipient_id], NOTIFICATION_EVENT)
