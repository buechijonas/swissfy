from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission

from commons.i18n import local_datetime
from swissfy.accounts.roles import is_moderator, outranks

from .models import Suspension


class IsNotAuthor(BasePermission):
    message = _("You cannot report your own content.")

    def has_object_permission(self, request, view, obj):
        return obj.author_id != request.user.pk


class CanReportAuthor(BasePermission):
    message = _("You cannot report content by admins.")

    def has_object_permission(self, request, view, obj):
        return not (is_moderator(request.user) and outranks(obj.author, request.user))


class CanModerateAuthor(BasePermission):
    message = _("Only admins can moderate content by admins.")

    def has_object_permission(self, request, view, obj):
        return not outranks(obj.author, request.user)


class CanViewWarnings(BasePermission):
    message = _("You cannot see these warnings.")

    def has_object_permission(self, request, view, obj):
        return obj == request.user or is_moderator(request.user)


class IsNotSuspended(BasePermission):
    def has_permission(self, request, view):
        suspensions = Suspension.objects.filter(user=request.user)
        if not suspensions.running().exists():
            return True
        lifted_at = suspensions.lifted_at()
        if lifted_at is None:
            self.message = _("Your account is suspended permanently.")
        else:
            until = local_datetime(lifted_at)
            self.message = _("Your account is suspended until %(until)s.") % {"until": until}
        return False
