from rest_framework.permissions import BasePermission

from swissfy.moderation.sanctions import is_suspended, suspension_message


class IsAuthor(BasePermission):
    message = "Du kannst nur eigene Inhalte bearbeiten."

    def has_object_permission(self, request, view, obj):
        return obj.author_id == request.user.pk


class IsNotSuspended(BasePermission):
    def has_permission(self, request, view):
        if is_suspended(request.user):
            self.message = suspension_message(request.user)
            return False
        return True
