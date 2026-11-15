from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models, transaction
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from commons.models import BaseModel, BaseQuerySet, UUIDModel, boolean, count_of
from swissfy.accounts.models import UserProfile
from swissfy.accounts.roles import Role, is_admin, is_moderator
from swissfy.moderation.models import Report, Suspension, Warning, convert_warning_integrity_error
from swissfy.social.models import Follow, Friendship

TEXT_LENGTH = 500
NAME_LENGTH = 50

NOT_HIDDEN = Q(hidden_at__isnull=True)


class Audience(models.TextChoices):
    PUBLIC = "public", _("Alle")
    FOLLOWERS = "followers", _("Follower")
    FRIENDS = "friends", _("Freunde")
    GROUPS = "groups", _("Gruppen")
    GLOBAL = "global", _("Global")


def by_suspended_author():
    return Q(author__in=Suspension.objects.running().values("user"))


def by_admin_author():
    return Q(Exists(Group.objects.filter(user=OuterRef("author"), name=Role.ADMIN.label)))


def reportable_by(user):
    reportable = ~Q(author=user)
    if is_moderator(user) and not is_admin(user):
        reportable &= ~by_admin_author()
    return boolean(reportable)


def followed_by(user):
    followed = Follow.objects.filter(follower=user).values("following")
    friends = Friendship.objects.filter(user=user).values("friend")
    return followed.union(friends)


def shared_with_viewer():
    Profile = UserProfile.Visibility
    profile_visible = (
        Q(author__profile__profile_visibility=Profile.PUBLIC)
        | Q(author__profile__profile_visibility=Profile.FOLLOWERS, viewer_follows=True)
        | Q(viewer_is_friend=True)
    )
    audience = (
        Q(visibility=Audience.PUBLIC)
        | Q(visibility=Audience.FOLLOWERS, viewer_follows=True)
        | Q(visibility=Audience.FRIENDS, viewer_is_friend=True)
        | Q(visibility=Audience.GROUPS, viewer_in_group=True)
    )
    return profile_visible & audience


class AudienceQuerySet(BaseQuerySet):
    def with_audience(self, user, groups):
        return self.filter(author__is_active=True).annotate(
            viewer_follows=Exists(
                Follow.objects.filter(follower=user, following=OuterRef("author"))
            ),
            viewer_is_friend=Exists(
                Friendship.objects.filter(user=user, friend=OuterRef("author"))
            ),
            viewer_in_group=Exists(groups.filter(members=user)),
        )


class ContactGroup(BaseModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contact_groups"
    )
    name = models.CharField(max_length=NAME_LENGTH)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="+", blank=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "name"], name="unique_contact_group"),
        ]

    def __str__(self):
        return f"{self.owner}: {self.name}"


class HideableModel(UUIDModel):
    hidden_at = models.DateTimeField(null=True, blank=True)

    class Meta(UUIDModel.Meta):
        abstract = True

    @property
    def is_hidden(self):
        return self.hidden_at is not None

    def hide(self):
        self.hidden_at = timezone.now()
        self.save(update_fields=["hidden_at"])

    @transaction.atomic
    def warn(self, moderator, reason):
        warning = self.new_warning(moderator, reason)
        with convert_warning_integrity_error(), transaction.atomic():
            warning.save()
        self.reports.resolve()
        self.hide()
        return warning


class ModeratedQuerySet(BaseQuerySet):
    target_field = None

    def with_moderation(self, user):
        warnings = Warning.objects.all()
        moderation = self.annotate(
            open_report_count=count_of(Report.objects.open(), self.target_field),
            is_warned=boolean(Q(pk__in=warnings.values(self.target_field))),
        )
        if is_admin(user):
            return moderation.annotate(can_warn=boolean(Q(is_warned=False)))
        return moderation.annotate(can_warn=boolean(Q(is_warned=False) & ~by_admin_author()))
