from django.utils import timezone

from swissfy.accounts.roles import Role, role_of, set_role
from swissfy.notifications.models import Notification
from swissfy.notifications.notify import notify

from .models import SUSPENSION_STEPS, Suspension, Warning

LOCKED_FOREVER = "forever"
WARNINGS_BEFORE_SUSPENSION = 3


def suspended_users():
    return Suspension.objects.running().values("user")


def is_suspended(user):
    return Suspension.objects.running().filter(user=user).exists()


def suspension_message(user):
    ends = Suspension.objects.filter(user=user).pending().values_list("ends_at", flat=True)
    ends = list(ends)
    if None in ends:
        return "Dein Konto ist dauerhaft gesperrt."
    until = timezone.localtime(max(ends)).strftime("%d.%m.%Y, %H:%M Uhr")
    return f"Dein Konto ist bis {until} gesperrt."


def next_suspension_start(user, now):
    ends = list(Suspension.objects.filter(user=user).pending(now).values_list("ends_at", flat=True))
    if None in ends:
        return None
    return max(ends, default=now)


def suspend_if_needed(warning):
    now = timezone.now()
    count = Warning.objects.filter(user=warning.user).active(now).count()
    if count < WARNINGS_BEFORE_SUSPENSION:
        return None
    starts_at = next_suspension_start(warning.user, now)
    if starts_at is None:
        return None
    step = min(count - WARNINGS_BEFORE_SUSPENSION, len(SUSPENSION_STEPS) - 1)
    return suspend(warning.user, warning, step, starts_at)


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


def issue_warning(target, field, moderator, reason):
    warning = Warning.objects.create(
        user_id=target.author_id, moderator=moderator, reason=reason, **{field: target}
    )
    target.reports.resolve()
    target.hide()
    notify(warning.user, Notification.Kind.WARNING, warning=warning)
    suspend_if_needed(warning)
    return warning


def role_locked_until(user):
    now = timezone.now()
    if not Suspension.objects.filter(user=user).exists():
        return None
    pending = list(
        Suspension.objects.filter(user=user).pending(now).values_list("ends_at", flat=True)
    )
    if None in pending:
        return LOCKED_FOREVER
    expiries = [warning.expires_at for warning in Warning.objects.filter(user=user).active(now)]
    return max(pending + expiries, default=None)
