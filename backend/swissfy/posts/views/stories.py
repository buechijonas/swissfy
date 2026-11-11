from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from commons.views import BaseViewSet, CreateModelMixin
from main.parsers import JSONParser

from ..models import Story, StoryLike, StoryView
from ..permissions import IsNotSuspended
from ..serializers import StoryModelSerializer
from .media import serve_image


class StoryViewSet(BaseViewSet, CreateModelMixin):
    serializer_class = StoryModelSerializer
    parser_classes = [MultiPartParser, JSONParser]
    lookup_field = "uuid"
    lookup_value_converter = "uuid"
    permission_action_classes = {"create": [IsAuthenticated, IsNotSuspended]}

    def get_queryset(self):
        return Story.objects.apply_acl(self.request.user).with_details(self.request.user)

    def destroy(self, request, uuid):
        get_object_or_404(Story, uuid=uuid, author=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def record_view(self, story):
        StoryView.objects.get_or_create(user=self.request.user, story=story)

    @action(detail=True, methods=["post"])
    def view(self, request, uuid):
        self.record_view(self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def like(self, request, uuid):
        story = self.get_object()
        StoryLike.objects.get_or_create(user=request.user, story=story)
        self.record_view(story)
        return self.respond(story)

    @like.mapping.delete
    def unlike(self, request, uuid):
        story = self.get_object()
        StoryLike.objects.filter(user=request.user, story=story).delete()
        return self.respond(story)

    @action(detail=True)
    def image(self, request, uuid):
        return serve_image(self.get_object().image)
