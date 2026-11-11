from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from swissfy.accounts.roles import is_admin
from swissfy.social.serializers import can_view_profile
from swissfy.social.views import ProfileView

from .catalog import achievements_of


class AchievementsView(ProfileView):
    def get(self, request, username):
        target = self.get_target(request, username)
        if not can_view_profile(request.user, target):
            raise PermissionDenied("Du kannst die Erfolge dieses Profils nicht sehen.")
        return Response(achievements_of(target, reveal_secrets=is_admin(request.user)))
