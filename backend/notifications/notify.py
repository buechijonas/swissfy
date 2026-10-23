from django.db.models import Exists, OuterRef
from django.utils import timezone

from moderation.models import WARNING_EXPIRY, Warning

from .models import Notification

Kind = Notification.Kind


def notify(recipient, kind, actor=None, **targets):
    if actor is not None and actor.pk == recipient.pk:
        return None
    return Notification.objects.create(recipient=recipient, kind=kind, actor=actor, **targets)


def withdraw(recipient, kind, actor, **targets):
    Notification.objects.filter(recipient=recipient, kind=kind, actor=actor, **targets).delete()


def resolve_request(recipient, kind, actor, resolution):
    Notification.objects.filter(recipient=recipient, actor=actor, kind=kind, resolution="").update(
        resolution=resolution
    )


def sync_expired_warnings(user):
    now = timezone.now()
    notified = Notification.objects.filter(warning=OuterRef("pk"), kind=Kind.WARNING_EXPIRED)
    expired = Warning.objects.filter(user=user, created_at__lte=now - WARNING_EXPIRY).exclude(
        Exists(notified)
    )
    Notification.objects.bulk_create(
        [
            Notification(
                recipient=user,
                kind=Kind.WARNING_EXPIRED,
                warning=warning,
                created_at=warning.created_at + WARNING_EXPIRY,
            )
            for warning in expired
        ],
        ignore_conflicts=True,
    )
