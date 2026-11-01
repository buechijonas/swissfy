from rest_framework import mixins

from commons.views import BaseViewSet, CreateModelMixin, UpdateModelMixin

from ..models import ContactGroup, SavedFolder
from ..serializers import ContactGroupModelSerializer, SavedFolderModelSerializer


class OwnedViewSet(
    BaseViewSet,
    mixins.ListModelMixin,
    CreateModelMixin,
    mixins.RetrieveModelMixin,
    UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    pagination_class = None

    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        return serializer.save(owner=self.request.user)


class SavedFolderViewSet(OwnedViewSet):
    model = SavedFolder
    serializer_class = SavedFolderModelSerializer


class ContactGroupViewSet(OwnedViewSet):
    model = ContactGroup
    serializer_class = ContactGroupModelSerializer

    def get_queryset(self):
        return super().get_queryset().prefetch_related("members")
