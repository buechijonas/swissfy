from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission

from swissfy.accounts.roles import is_moderator, outranks


class IsNotAuthor(BasePermission):
    message = _("Du kannst eigene Inhalte nicht melden.")

    def has_object_permission(self, request, view, obj):
        return obj.author_id != request.user.pk


class CanReportAuthor(BasePermission):
    message = _("Inhalte von Admins kannst du nicht melden.")

    def has_object_permission(self, request, view, obj):
        return not (is_moderator(request.user) and outranks(obj.author, request.user))


class CanModerateAuthor(BasePermission):
    message = _("Inhalte von Admins können nur Admins bearbeiten.")

    def has_object_permission(self, request, view, obj):
        return not outranks(obj.author, request.user)


class CanViewWarnings(BasePermission):
    message = _("Du kannst diese Verwarnungen nicht sehen.")

    def has_object_permission(self, request, view, obj):
        return obj == request.user or is_moderator(request.user)
