import re

from django.http import FileResponse, HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Post, PostImage
from .posts import visible_post

BYTE_RANGE = re.compile(r"bytes=(\d*)-(\d*)$")
CHUNK_SIZE = 64 * 1024


def serve_image(file):
    response = FileResponse(file.open("rb"), content_type="image/webp")
    response["Cache-Control"] = "private, max-age=31536000, immutable"
    return response


def read_range(file, start, length):
    try:
        file.seek(start)
        while length > 0:
            chunk = file.read(min(CHUNK_SIZE, length))
            if not chunk:
                break
            length -= len(chunk)
            yield chunk
    finally:
        file.close()


def serve_video(request, file):
    size = file.size
    match = BYTE_RANGE.match(request.headers.get("Range", ""))
    if not match or match.groups() == ("", ""):
        response = FileResponse(file.open("rb"), content_type="video/mp4")
    else:
        first, last = match.groups()
        if first:
            start, end = int(first), min(int(last), size - 1) if last else size - 1
        else:
            start, end = max(0, size - int(last)), size - 1
        if start > end:
            return HttpResponse(status=416, headers={"Content-Range": f"bytes */{size}"})
        response = StreamingHttpResponse(
            read_range(file.open("rb"), start, end - start + 1),
            status=206,
            content_type="video/mp4",
        )
        response["Content-Length"] = end - start + 1
        response["Content-Range"] = f"bytes {start}-{end}/{size}"
    response["Accept-Ranges"] = "bytes"
    response["Cache-Control"] = "private, max-age=31536000, immutable"
    return response


class PostImageView(APIView):
    def get(self, request, uuid, position):
        image = get_object_or_404(PostImage, post=visible_post(request, uuid), position=position)
        return serve_image(image.file)


class PostVideoView(APIView):
    def get(self, request, uuid):
        post = visible_post(request, uuid)
        if post.video_status != Post.VideoStatus.READY:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return serve_video(request, post.video)


class PostThumbnailView(APIView):
    def get(self, request, uuid):
        thumbnail = visible_post(request, uuid).thumbnail
        if not thumbnail:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return serve_image(thumbnail)
