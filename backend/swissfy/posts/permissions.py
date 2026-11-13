from django.utils import timezone
from rest_framework.exceptions import Throttled
from rest_framework.permissions import BasePermission

from swissfy.moderation.models import Suspension

from .models import POSTS_PER_DAY, PostCreation


class IsAuthor(BasePermission):
    message = "Du kannst nur eigene Inhalte bearbeiten."

    def has_object_permission(self, request, view, obj):
        return obj.author_id == request.user.pk


class IsNotSuspended(BasePermission):
    def has_permission(self, request, view):
        suspensions = Suspension.objects.filter(user=request.user)
        if not suspensions.running().exists():
            return True
        lifted_at = suspensions.lifted_at()
        if lifted_at is None:
            self.message = "Dein Konto ist dauerhaft gesperrt."
        else:
            until = timezone.localtime(lifted_at).strftime("%d.%m.%Y, %H:%M Uhr")
            self.message = f"Dein Konto ist bis {until} gesperrt."
        return False


class HasPostQuota(BasePermission):
    def has_permission(self, request, view):
        if not PostCreation.objects.remaining(request.user):
            raise Throttled(detail=f"Du kannst höchstens {POSTS_PER_DAY} Feeds pro Tag erstellen.")
        return True
