from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import Throttled
from rest_framework.permissions import BasePermission

from commons.i18n import local_datetime
from swissfy.moderation.models import Suspension

from .models import POSTS_PER_DAY, PostCreation


class IsAuthor(BasePermission):
    message = _("Du kannst nur eigene Inhalte bearbeiten.")

    def has_object_permission(self, request, view, obj):
        return obj.author_id == request.user.pk


class IsNotSuspended(BasePermission):
    def has_permission(self, request, view):
        suspensions = Suspension.objects.filter(user=request.user)
        if not suspensions.running().exists():
            return True
        lifted_at = suspensions.lifted_at()
        if lifted_at is None:
            self.message = _("Dein Konto ist dauerhaft gesperrt.")
        else:
            until = local_datetime(lifted_at)
            self.message = _("Dein Konto ist bis %(until)s gesperrt.") % {"until": until}
        return False


class HasPostQuota(BasePermission):
    def has_permission(self, request, view):
        if not PostCreation.objects.remaining(request.user):
            limit = _("Du kannst höchstens %(count)s Feeds pro Tag erstellen.")
            raise Throttled(detail=limit % {"count": POSTS_PER_DAY})
        return True
