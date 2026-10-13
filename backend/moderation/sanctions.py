from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from accounts.roles import Role, role_of, set_role
from notifications.models import Notification
from notifications.notify import notify

from .models import WARNING_EXPIRY, Suspension, Warning

LOCKED_FOREVER = "forever"
WARNINGS_BEFORE_SUSPENSION = 3
SUSPENSION_STEPS = [
    (timedelta(days=3), "3 Tage"),
    (timedelta(weeks=1), "1 Woche"),
    (timedelta(days=30), "1 Monat"),
    (timedelta(days=365), "1 Jahr"),
    (None, "Lebenslang"),
]


def warning_expires_at(warning):
    return warning.created_at + WARNING_EXPIRY


def running(now=None):
    now = now or timezone.now()
    return Q(starts_at__lte=now) & (Q(ends_at__isnull=True) | Q(ends_at__gt=now))


def suspended_users():
    return Suspension.objects.filter(running()).values("user")


def pending_suspensions(user, now):
    return Suspension.objects.filter(Q(ends_at__isnull=True) | Q(ends_at__gt=now), user=user)


def suspend_if_needed(warning):
    now = timezone.now()
    count = Warning.objects.filter(user=warning.user, created_at__gt=now - WARNING_EXPIRY).count()
    if count < WARNINGS_BEFORE_SUSPENSION:
        return None
    pending = list(pending_suspensions(warning.user, now))
    if any(suspension.ends_at is None for suspension in pending):
        return None
    latest_end = max((suspension.ends_at for suspension in pending), default=now)
    step = min(count - WARNINGS_BEFORE_SUSPENSION, len(SUSPENSION_STEPS) - 1)
    return suspend(warning.user, warning, step, latest_end)


def suspend(user, warning, step, starts_at):
    duration = SUSPENSION_STEPS[step][0]
    suspension = Suspension.objects.create(
        user=user,
        warning=warning,
        step=step,
        starts_at=starts_at,
        ends_at=starts_at + duration if duration else None,
    )
    if role_of(user) == Role.VERIFIED:
        set_role(user, Role.DEFAULT)
    notify(user, Notification.Kind.SUSPENSION, suspension=suspension)
    return suspension


def role_locked_until(user):
    now = timezone.now()
    if not Suspension.objects.filter(user=user).exists():
        return None
    pending = [suspension.ends_at for suspension in pending_suspensions(user, now)]
    if None in pending:
        return LOCKED_FOREVER
    active = Warning.objects.filter(user=user, created_at__gt=now - WARNING_EXPIRY)
    expiries = [warning.created_at + WARNING_EXPIRY for warning in active]
    return max(pending + expiries, default=None)


def suspension_message(user):
    ends = [suspension.ends_at for suspension in pending_suspensions(user, timezone.now())]
    if None in ends:
        return "Dein Konto ist dauerhaft gesperrt."
    until = timezone.localtime(max(ends)).strftime("%d.%m.%Y, %H:%M Uhr")
    return f"Dein Konto ist bis {until} gesperrt."


def is_suspended(user):
    return Suspension.objects.filter(running(), user=user).exists()


def ensure_not_suspended(user):
    if is_suspended(user):
        raise PermissionDenied(suspension_message(user))
