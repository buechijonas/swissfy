from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import Throttled
from rest_framework.permissions import BasePermission

from .models import POSTS_PER_DAY, PostCreation


class IsAuthor(BasePermission):
    message = _("You can only edit your own content.")

    def has_object_permission(self, request, view, obj):
        return obj.author_id == request.user.pk


class HasPostQuota(BasePermission):
    def has_permission(self, request, view):
        if not PostCreation.objects.remaining(request.user):
            limit = _("You can create at most %(count)s feeds per day.")
            raise Throttled(detail=limit % {"count": POSTS_PER_DAY})
        return True
