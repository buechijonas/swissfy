from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Exists, Max, OuterRef, Subquery
from django.utils import timezone

from swissfy.accounts.roles import Role, role_of, set_role
from swissfy.notifications.models import Notification
from swissfy.notifications.notify import notify

from .models import (
    SUSPENSION_STEPS,
    WARNING_EXPIRY,
    Suspension,
    Warning,
    convert_warning_integrity_error,
)

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


@transaction.atomic
def issue_warning(target, moderator, reason):
    warning = target.new_warning(moderator, reason)
    with convert_warning_integrity_error(), transaction.atomic():
        warning.save()
    target.reports.resolve()
    target.hide()
    notify(warning.user, Notification.Kind.WARNING, warning=warning)
    suspend_if_needed(warning)
    return warning


def latest(queryset, field):
    values = queryset.order_by().values("user").annotate(latest=Max(field)).values("latest")
    return Subquery(values[:1])


def annotate_role_lock(users, now=None):
    now = now or timezone.now()
    suspensions = Suspension.objects.filter(user=OuterRef("pk"))
    warnings = Warning.objects.filter(user=OuterRef("pk")).active(now)
    return users.annotate(
        has_suspension=Exists(suspensions),
        locked_forever=Exists(suspensions.filter(ends_at__isnull=True)),
        latest_suspension_end=latest(suspensions.filter(ends_at__gt=now), "ends_at"),
        latest_warning_at=latest(warnings, "created_at"),
    )


def role_lock(user):
    if not user.has_suspension:
        return None
    if user.locked_forever:
        return LOCKED_FOREVER
    warning_expiry = user.latest_warning_at and user.latest_warning_at + WARNING_EXPIRY
    return max(filter(None, [user.latest_suspension_end, warning_expiry]), default=None)


def role_locked_until(user):
    users = get_user_model().objects.filter(pk=user.pk)
    return role_lock(annotate_role_lock(users).get())
