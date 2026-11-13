from django.conf import settings
from django.db import models
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from commons.models import BaseModel, BaseQuerySet
from swissfy.moderation.models import WARNING_EXPIRY, Suspension, Warning
from swissfy.posts.models import authors_for
from swissfy.social.models import Follow, FollowRequest, FriendRequest, Friendship

PREVIEW_LENGTH = 80


def local_date(value):
    return timezone.localtime(value).strftime("%d.%m.%Y")


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

    def mark_read(self):
        return self.unread().update(read_at=timezone.now())

    def withdraw(self, recipient, kind, actor, **targets):
        return self.filter(recipient=recipient, kind=kind, actor=actor, **targets).delete()

    def resolve_request(self, recipient, kind, actor, resolution):
        requests = self.filter(recipient=recipient, actor=actor, kind=kind, resolution="")
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
                return f"Du wurdest verwarnt: {self.warning.get_reason_display()}."
            case Kind.WARNING_EXPIRED:
                reason = self.warning.get_reason_display()
                created = local_date(self.warning.created_at)
                return f"Deine Verwarnung «{reason}» vom {created} ist verjährt."
            case Kind.SUSPENSION:
                return self.suspension_message
            case Kind.COMMENT:
                return f"{self.actor_name} hat deinen Feed kommentiert: {quote(self.comment.text)}"
            case Kind.LIKE:
                return f"{self.actor_name} gefällt dein Feed."
            case Kind.FOLLOW:
                return f"{self.actor_name} folgt dir jetzt."
            case Kind.FOLLOW_REQUEST:
                return f"{self.actor_name} möchte dir folgen."
            case Kind.FRIEND_REQUEST:
                return f"{self.actor_name} möchte mit dir befreundet sein."
        return ""

    @property
    def suspension_message(self):
        suspension = self.suspension
        duration = suspension.duration_label
        if suspension.ends_at is None:
            return "Dein Konto wurde dauerhaft gesperrt."
        until = local_date(suspension.ends_at)
        if suspension.starts_at > timezone.now():
            start = local_date(suspension.starts_at)
            return f"Dein Konto wird für {duration} gesperrt, ab {start} bis {until}."
        return f"Dein Konto wurde für {duration} gesperrt, bis {until}."

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
