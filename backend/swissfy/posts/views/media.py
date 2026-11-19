from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from commons.media import serve_image, serve_video
from commons.views import BaseViewSet

from ..models import Post, PostImage


class PostMediaViewSet(BaseViewSet):
    lookup_field = "uuid"
    lookup_value_converter = "uuid"
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Post.objects.apply_acl(self.request.user)

    @action(detail=True, url_path="images/<int:position>")
    def image(self, request, uuid, position):
        image = get_object_or_404(PostImage, post=self.get_object(), position=position)
        return serve_image(image.file)

    @action(detail=True)
    def video(self, request, uuid):
        post = self.get_object()
        if not post.has_video:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return serve_video(request, post.video)

    @action(detail=True)
    def thumbnail(self, request, uuid):
        thumbnail = self.get_object().thumbnail
        if not thumbnail:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return serve_image(thumbnail)
