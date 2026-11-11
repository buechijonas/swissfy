from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny

from .models import Changelog
from .serializers import ChangelogSerializer


class ChangelogViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    serializer_class = ChangelogSerializer
    permission_classes = [AllowAny]
    lookup_field = "version"

    def get_queryset(self):
        return Changelog.all()

    def get_object(self):
        return Changelog.get(self.kwargs["version"])
