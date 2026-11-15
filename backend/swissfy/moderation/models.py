from contextlib import contextmanager
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, models
from django.db.models import Count, Max, Q
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _

from commons.models import BaseModel, BaseQuerySet
from swissfy.accounts.roles import Role, is_admin, role_of, set_role


class Reason(models.TextChoices):
    ANTISEMITISM = "antisemitism", _("Antisemitismus")
    EXPLOITATION = "exploitation", _("Ausbeuterische Inhalte")
    INSULT = "insult", _("Beleidigung")
    REWARD_HUNTING = "reward_hunting", _("Belohnungsjagd")
    HARASSMENT = "harassment", _("Belästigung")
    FRAUD = "fraud", _("Betrug")
    CHRISTOPHOBIA = "christophobia", _("Christophobie")
    CYBERGROOMING = "cybergrooming", _("Cybergrooming")
    CYBERBULLYING = "cyberbullying", _("Cybermobbing")
    DISCRIMINATION = "discrimination", _("Diskriminierung")
    DOXXING = "doxxing", _("Doxxing")
    THREAT = "threat", _("Drohung")
    EXTORTION = "extortion", _("Erpressung")
    MISINFORMATION = "misinformation", _("Falschinformationen")
    FASCISM = "fascism", _("Faschismus")
    XENOPHOBIA = "xenophobia", _("Fremdenfeindlichkeit")
    CONSPIRACY = "conspiracy", _("Gefährliche Verschwörungstheorien")
    VIOLENT_CONTENT = "violent_content", _("Gewaltbasierter Inhalt")
    GLORIFYING_VIOLENCE = "glorifying_violence", _("Gewaltverherrlichung")
    HATE_SPEECH = "hate_speech", _("Hassrede")
    HOMOPHOBIA = "homophobia", _("Homophobie")
    IDENTITY_THEFT = "identity_theft", _("Identitätsdiebstahl")
    ILLEGAL_CONTENT = "illegal_content", _("Illegale Inhalte")
    ISLAMOPHOBIA = "islamophobia", _("Islamophobie")
    CULTURAL_APPROPRIATION = "cultural_appropriation", _("Kulturelle Aneignung")
    PROTECTION_OF_MINORS = "protection_of_minors", _("Minderjährigenschutz")
    PRIVILEGE_ABUSE = "privilege_abuse", _("Missbrauch von Privilegien")
    PLAGIARISM = "plagiarism", _("Plagiate")
    PORNOGRAPHY = "pornography", _("Pornografische Inhalte")
    PROPAGANDA = "propaganda", _("Propaganda")
    RACISM = "racism", _("Rassismus")
    RELATIVIZATION = "relativization", _("Relativierung")
    SELF_HARM = "self_harm", _("Selbstgefährdung")
    VIGILANTISM = "vigilantism", _("Selbstjustiz")
    SEXISM = "sexism", _("Sexismus")
    SEXTORTION = "sextortion", _("Sextortion")
    SPAM = "spam", _("Spam")
    INAPPROPRIATE_LANGUAGE = "inappropriate_language", _("Unangemessene Wortwahl")
    UNETHICAL_ADVERTISING = "unethical_advertising", _("Unethische Werbung")
    WHATABOUTISM = "whataboutism", _("Whataboutismus")

    @classmethod
    def options(cls):
        return [{"value": value, "label": label} for value, label in cls.choices]


class AlreadyWarned(Exception):
    pass


@contextmanager
def convert_warning_integrity_error():
    try:
        yield
    except IntegrityError as exc:
        raise AlreadyWarned() from exc


WARNING_EXPIRY = timedelta(days=90)
SUSPENSION_STEPS = [
    (timedelta(days=3), _("3 Tage")),
    (timedelta(weeks=1), _("1 Woche")),
    (timedelta(days=30), _("1 Monat")),
    (timedelta(days=365), _("1 Jahr")),
    (None, _("Lebenslang")),
]
WARNINGS_BEFORE_SUSPENSION = 3
LOCKED_FOREVER = "forever"

ONE_TARGET = Q(post__isnull=False, comment__isnull=True) | Q(
    post__isnull=True, comment__isnull=False
)


def by_admin():
    admin = Role.ADMIN.label
    return Q(post__author__groups__name=admin) | Q(comment__author__groups__name=admin)


class ReportQuerySet(BaseQuerySet):
    def open(self):
        return self.filter(resolved_at=None)

    def resolved(self):
        return self.filter(resolved_at__isnull=False)

    def resolve(self):
        return self.open().update(resolved_at=timezone.now())

    def closed_targets(self):
        open_reports = Report.objects.open()
        return (
            self.resolved()
            .exclude(post__in=open_reports.values("post"))
            .exclude(comment__in=open_reports.values("comment"))
        )

    def queue(self, viewer, resolved):
        reports = self.closed_targets() if resolved else self.open()
        if not is_admin(viewer):
            reports = reports.exclude(by_admin())
        last_activity = Max("resolved_at" if resolved else "created_at")
        return (
            reports.values("post", "comment")
            .annotate(report_count=Count("id"), last_activity=last_activity)
            .order_by("-last_activity")
        )

    def about(self, user):
        return (
            self.filter(Q(post__author=user) | Q(comment__author=user))
            .values("post", "post__uuid", "post__text", "comment", "comment__uuid", "comment__text")
            .annotate(
                report_count=Count("id"),
                open_count=Count("id", filter=Q(resolved_at=None)),
                last_reported_at=Max("created_at"),
            )
            .order_by("-last_reported_at")
        )


class Report(BaseModel):
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )
    post = models.ForeignKey(
        "posts.Post", on_delete=models.CASCADE, null=True, blank=True, related_name="reports"
    )
    comment = models.ForeignKey(
        "posts.Comment", on_delete=models.CASCADE, null=True, blank=True, related_name="reports"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    objects = ReportQuerySet.as_manager()

    class Meta:
        constraints = [
            models.CheckConstraint(condition=ONE_TARGET, name="report_one_target"),
            models.UniqueConstraint(fields=["reporter", "post"], name="unique_post_report"),
            models.UniqueConstraint(fields=["reporter", "comment"], name="unique_comment_report"),
        ]
        indexes = [
            models.Index(
                fields=["post", "comment"],
                condition=Q(resolved_at__isnull=True),
                name="open_reports",
            )
        ]


class WarningQuerySet(BaseQuerySet):
    def active(self, now=None):
        return self.filter(created_at__gt=(now or timezone.now()) - WARNING_EXPIRY)


class Warning(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="warnings"
    )
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    reason = models.CharField(max_length=40, choices=Reason.choices)
    post = models.ForeignKey("posts.Post", on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.ForeignKey("posts.Comment", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    event_type = "warning"

    objects = WarningQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["post"], condition=Q(post__isnull=False), name="one_warning_per_post"
            ),
            models.UniqueConstraint(
                fields=["comment"],
                condition=Q(comment__isnull=False),
                name="one_warning_per_comment",
            ),
        ]

    @property
    def expires_at(self):
        return self.created_at + WARNING_EXPIRY

    @property
    def is_expired(self):
        return self.expires_at <= timezone.now()

    @property
    def is_past(self):
        return self.is_expired

    @property
    def target_label(self):
        if self.comment_id:
            return _("Kommentar")
        return _("Feed") if self.post_id else None

    @property
    def moderation_link(self):
        if self.comment_id:
            return f"/moderation/comments/{self.comment.uuid}"
        return f"/moderation/posts/{self.post.uuid}" if self.post_id else None

    def suspend_if_needed(self):
        now = timezone.now()
        count = Warning.objects.filter(user=self.user).active(now).count()
        if count < WARNINGS_BEFORE_SUSPENSION:
            return None
        starts_at = Suspension.objects.filter(user=self.user).lifted_at(now)
        if starts_at is None:
            return None
        step = min(count - WARNINGS_BEFORE_SUSPENSION, len(SUSPENSION_STEPS) - 1)
        return Suspension.start(self.user, self, step, starts_at)


class SuspensionQuerySet(BaseQuerySet):
    def running(self, now=None):
        now = now or timezone.now()
        return self.filter(Q(starts_at__lte=now), Q(ends_at__isnull=True) | Q(ends_at__gt=now))

    def pending(self, now=None):
        return self.filter(Q(ends_at__isnull=True) | Q(ends_at__gt=now or timezone.now()))

    def lifted_at(self, now=None):
        now = now or timezone.now()
        ends = list(self.pending(now).values_list("ends_at", flat=True))
        return None if None in ends else max(ends, default=now)


class Suspension(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="suspensions"
    )
    warning = models.ForeignKey(Warning, on_delete=models.SET_NULL, null=True, related_name="+")
    step = models.PositiveSmallIntegerField()
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    event_type = "suspension"

    objects = SuspensionQuerySet.as_manager()

    class Meta:
        ordering = ["-starts_at"]
        indexes = [models.Index(fields=["user", "ends_at"], name="suspension_user_end")]

    @classmethod
    def start(cls, user, warning, step, starts_at):
        duration = SUSPENSION_STEPS[step][0]
        suspension = cls.objects.create(
            user=user,
            warning=warning,
            step=step,
            starts_at=starts_at,
            ends_at=starts_at + duration if duration else None,
        )
        if role_of(user) == Role.VERIFIED:
            set_role(user, Role.DEFAULT)
        return suspension

    @property
    def duration_label(self):
        return SUSPENSION_STEPS[self.step][1]

    @property
    def caused_at(self):
        return self.warning.created_at if self.warning else self.starts_at

    @property
    def state(self):
        now = timezone.now()
        if self.starts_at > now:
            return "scheduled"
        return "ended" if self.ends_at and self.ends_at <= now else "active"

    @property
    def is_past(self):
        return self.state == "ended"

    @property
    def status_text(self):
        ends_at = self.ends_at and timezone.localtime(self.ends_at)
        until = {"until": date_format(ends_at, _("j. F Y"))} if ends_at else None
        if self.state == "ended":
            return _("Abgelaufen am %(until)s") % until
        if self.state == "scheduled":
            if until:
                return _("Beginnt nach der laufenden Sperre, bis %(until)s") % until
            return _("Beginnt nach der laufenden Sperre, dauerhaft")
        return _("Gesperrt bis %(until)s") % until if until else _("Dauerhaft gesperrt")
