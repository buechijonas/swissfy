from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from main.parsers import JSONParser
from moderation.sanctions import ensure_not_suspended

from ..models import Story, StoryLike, StoryView
from ..queries import story_details, visible_stories
from ..serializers import StoryCreateSerializer, StorySerializer
from .media import serve_image


class StoryCreateView(APIView):
    parser_classes = [MultiPartParser, JSONParser]

    def post(self, request):
        ensure_not_suspended(request.user)
        serializer = StoryCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        story = serializer.save()
        return Response(story_response(request, story).data, status=status.HTTP_201_CREATED)


class StoryDetailView(APIView):
    def delete(self, request, uuid):
        story = get_object_or_404(Story, uuid=uuid, author=request.user)
        story.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def story_response(request, story):
    story = story_details(Story.objects.filter(pk=story.pk), request.user).get()
    return StorySerializer(story, context={"request": request})


def record_view(story, user):
    StoryView.objects.get_or_create(user=user, story=story)


class StoryViewView(APIView):
    def post(self, request, uuid):
        record_view(get_object_or_404(visible_stories(request.user), uuid=uuid), request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class StoryLikeView(APIView):
    def post(self, request, uuid):
        story = get_object_or_404(visible_stories(request.user), uuid=uuid)
        StoryLike.objects.get_or_create(user=request.user, story=story)
        record_view(story, request.user)
        return self.state(request, story)

    def delete(self, request, uuid):
        story = get_object_or_404(visible_stories(request.user), uuid=uuid)
        StoryLike.objects.filter(user=request.user, story=story).delete()
        return self.state(request, story)

    def state(self, request, story):
        return Response(story_response(request, story).data)


class StoryImageView(APIView):
    def get(self, request, uuid):
        return serve_image(get_object_or_404(visible_stories(request.user), uuid=uuid).image)
