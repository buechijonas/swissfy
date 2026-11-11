from rest_framework import mixins
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from commons.views import BaseViewSet
from swissfy.accounts.roles import is_admin
from swissfy.social.users import can_view_profile, profile_target

from .catalog import achievements_of


class CanViewAchievements(BasePermission):
    message = "Du kannst die Erfolge dieses Profils nicht sehen."

    def has_object_permission(self, request, view, obj):
        return can_view_profile(request.user, obj)


class AchievementViewSet(BaseViewSet, mixins.RetrieveModelMixin):
    permission_classes = [IsAuthenticated, CanViewAchievements]

    def get_object(self):
        target = profile_target(self.request.user, self.kwargs["username"])
        self.check_object_permissions(self.request, target)
        return target

    def retrieve(self, request, *args, **kwargs):
        target = self.get_object()
        return Response(achievements_of(target, reveal_secrets=is_admin(request.user)))
