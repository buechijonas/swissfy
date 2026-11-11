from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from commons.views import BaseViewSet
from swissfy.accounts.roles import is_admin
from swissfy.social.models import Member

from .catalog import achievements_of


class CanViewAchievements(BasePermission):
    message = "Du kannst die Erfolge dieses Profils nicht sehen."

    def has_object_permission(self, request, view, obj):
        return Member.objects.can_view(request.user, obj)


class AchievementViewSet(BaseViewSet):
    lookup_field = "username"
    permission_classes = [IsAuthenticated, CanViewAchievements]

    def get_object(self):
        members = Member.objects.apply_acl(self.request.user)
        target = get_object_or_404(members, username=self.kwargs["username"])
        self.check_object_permissions(self.request, target)
        return target

    @action(detail=True)
    def achievements(self, request, username):
        target = self.get_object()
        return Response(achievements_of(target, reveal_secrets=is_admin(request.user)))
