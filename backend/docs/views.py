from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .changelogs import all_changelogs, changelog


class ChangelogListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(all_changelogs())


class ChangelogView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, version):
        found = changelog(version)
        if found is None:
            raise NotFound("Diese Version gibt es nicht.")
        return Response(found)
