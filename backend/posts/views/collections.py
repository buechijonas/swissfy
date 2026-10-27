from rest_framework import generics

from ..models import ContactGroup, SavedFolder
from ..serializers import ContactGroupSerializer, SavedFolderSerializer


class OwnedListView(generics.ListCreateAPIView):
    pagination_class = None

    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class OwnedDetailView(generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user)


class FolderListView(OwnedListView):
    model = SavedFolder
    serializer_class = SavedFolderSerializer


class FolderDetailView(OwnedDetailView):
    model = SavedFolder
    serializer_class = SavedFolderSerializer


class GroupListView(OwnedListView):
    model = ContactGroup
    serializer_class = ContactGroupSerializer

    def get_queryset(self):
        return super().get_queryset().prefetch_related("members")


class GroupDetailView(OwnedDetailView):
    model = ContactGroup
    serializer_class = ContactGroupSerializer
