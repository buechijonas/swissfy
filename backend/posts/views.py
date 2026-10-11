from datetime import timedelta
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, Throttled
from rest_framework.pagination import CursorPagination
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Comment,
    CommentVote,
    ContactGroup,
    Like,
    PostCreation,
    PostImage,
    SavedFolder,
    SavedPost,
)
from main.numbers import compact_number

from .queries import attach_latest_replies, comment_details, feed, visible_posts, with_details
from .serializers import (
    CommentSerializer,
    ContactGroupSerializer,
    PostCreateSerializer,
    PostSerializer,
    PostSummarySerializer,
    SavedFolderSerializer,
)

POSTS_PER_DAY = 10


class NewestFirst(CursorPagination):
    page_size = 25
    ordering = "-id"


class FeedOrder(NewestFirst):
    ordering = ("-day", "-viewer_is_friend", "-id")


class SavedOrder(NewestFirst):
    ordering = "-saved_at"


class OldestFirst(CursorPagination):
    page_size = 50
    ordering = "id"


def visible_post(request, uuid):
    return get_object_or_404(visible_posts(request.user), uuid=uuid)


def remaining_posts(user):
    creations = PostCreation.objects.filter(author=user)
    recent = creations.filter(created_at__gte=timezone.now() - timedelta(days=1))
    return max(0, POSTS_PER_DAY - recent.count())


def check_quota(user):
    if not remaining_posts(user):
        raise Throttled(detail=f"Du kannst höchstens {POSTS_PER_DAY} Posts pro Tag erstellen.")


def serve_image(file):
    response = FileResponse(file.open("rb"), content_type="image/webp")
    response["Cache-Control"] = "private, max-age=31536000, immutable"
    return response


class FeedView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    pagination_class = FeedOrder
    parser_classes = [MultiPartParser, JSONParser]

    def get_queryset(self):
        return with_details(feed(self.request.user), self.request.user)

    def create(self, request, *args, **kwargs):
        check_quota(request.user)
        serializer = PostCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=request.user.pk)
            check_quota(request.user)
            PostCreation.objects.filter(
                author=request.user, created_at__lt=timezone.now() - timedelta(days=1)
            ).delete()
            PostCreation.objects.create(author=request.user)
            created = serializer.save()
        post = with_details(visible_posts(request.user), request.user).get(pk=created.pk)
        return Response(
            PostSerializer(post, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class UserPostListView(generics.ListAPIView):
    serializer_class = PostSerializer
    pagination_class = NewestFirst

    def get_queryset(self):
        posts = visible_posts(self.request.user).filter(author__username=self.kwargs["username"])
        if self.request.query_params.get("images"):
            posts = posts.exclude(thumbnail="")
        return with_details(posts, self.request.user)


class ActivityView(APIView):
    def get(self, request, username):
        viewer = request.user
        posts = visible_posts(viewer).filter(author__username=username)
        comments = Comment.objects.filter(
            author__username=username, post__in=visible_posts(viewer).values("pk")
        )
        comments = comment_details(comments, viewer)
        before = parse_datetime(request.query_params.get("before", ""))
        if before:
            posts = posts.filter(created_at__lt=before)
            comments = comments.filter(created_at__lt=before)

        page_size = NewestFirst.page_size
        posts = list(with_details(posts, viewer).order_by("-created_at")[:page_size])
        comments = list(comments.order_by("-created_at")[:page_size])
        commented = with_details(visible_posts(viewer), viewer).in_bulk(
            {comment.post_id for comment in comments}
        )
        items = sorted(posts + comments, key=lambda item: item.created_at, reverse=True)
        items = items[:page_size]

        context = {"request": request}
        results = [
            (
                {
                    "type": "comment",
                    **CommentSerializer(item, context=context).data,
                    "post": PostSummarySerializer(commented[item.post_id], context=context).data,
                }
                if isinstance(item, Comment)
                else {"type": "post", **PostSerializer(item, context=context).data}
            )
            for item in items
        ]
        next_page = None
        if len(items) == page_size:
            next_page = f"?{urlencode({'before': items[-1].created_at.isoformat()})}"
        return Response({"results": results, "next": next_page})


class PostDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = PostSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return with_details(visible_posts(self.request.user), self.request.user)

    def perform_destroy(self, post):
        if post.author_id != self.request.user.pk:
            raise PermissionDenied("Du kannst nur eigene Posts löschen.")
        post.delete()


class PostQuotaView(APIView):
    def get(self, request):
        return Response({"limit": POSTS_PER_DAY, "remaining": remaining_posts(request.user)})


class PostImageView(APIView):
    def get(self, request, uuid, position):
        image = get_object_or_404(PostImage, post=visible_post(request, uuid), position=position)
        return serve_image(image.file)


class PostThumbnailView(APIView):
    def get(self, request, uuid):
        thumbnail = visible_post(request, uuid).thumbnail
        if not thumbnail:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return serve_image(thumbnail)


class LikeView(APIView):
    def post(self, request, uuid):
        post = visible_post(request, uuid)
        Like.objects.get_or_create(user=request.user, post=post)
        return self.state(post, True)

    def delete(self, request, uuid):
        post = visible_post(request, uuid)
        Like.objects.filter(user=request.user, post=post).delete()
        return self.state(post, False)

    def state(self, post, liked):
        return Response({"liked": liked, "like_count": compact_number(post.likes.count())})


class SaveView(APIView):
    def put(self, request, uuid):
        folder = request.data.get("folder")
        if folder is not None:
            folder = get_object_or_404(SavedFolder, pk=folder, owner=request.user)
        SavedPost.objects.update_or_create(
            user=request.user, post=visible_post(request, uuid), defaults={"folder": folder}
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, uuid):
        SavedPost.objects.filter(user=request.user, post=visible_post(request, uuid)).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def visible_comments(viewer):
    return comment_details(Comment.objects.filter(post__in=visible_posts(viewer)), viewer)


class CommentListView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    pagination_class = OldestFirst

    def get_queryset(self):
        post = visible_post(self.request, self.kwargs["uuid"])
        return comment_details(post.comments.filter(parent=None), self.request.user)

    def list(self, request, *args, **kwargs):
        page = attach_latest_replies(self.paginate_queryset(self.get_queryset()), request.user)
        return self.get_paginated_response(self.get_serializer(page, many=True).data)

    def perform_create(self, serializer):
        serializer.save(
            post=visible_post(self.request, self.kwargs["uuid"]), author=self.request.user
        )


class CommentReplyListView(CommentListView):
    def parent(self):
        return get_object_or_404(visible_comments(self.request.user), uuid=self.kwargs["uuid"])

    def get_queryset(self):
        return comment_details(self.parent().replies.all(), self.request.user)

    def perform_create(self, serializer):
        parent = self.parent()
        serializer.save(post=parent.post, parent=parent, author=self.request.user)


class CommentDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = CommentSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return visible_comments(self.request.user)

    def retrieve(self, request, *args, **kwargs):
        comment = self.get_object()
        chain = []
        parent_id = comment.parent_id
        while parent_id:
            chain.append(parent_id)
            parent_id = Comment.objects.values_list("parent_id", flat=True).get(pk=parent_id)
        ancestors = self.get_queryset().in_bulk(chain)
        post = with_details(visible_posts(request.user), request.user).get(pk=comment.post_id)
        context = self.get_serializer_context()
        return Response(
            {
                **self.get_serializer(comment).data,
                "ancestors": self.get_serializer(
                    [ancestors[pk] for pk in reversed(chain)], many=True
                ).data,
                "post": PostSummarySerializer(post, context=context).data,
            }
        )

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author_id != request.user.pk:
            raise PermissionDenied("Du kannst nur eigene Kommentare löschen.")
        comment.delete()

        parent = None
        if comment.parent_id:
            parent = self.get_queryset().get(pk=comment.parent_id)
            parent = attach_latest_replies([parent], request.user)[0]
            parent = self.get_serializer(parent).data
        comment_count = Comment.objects.filter(post=comment.post_id, parent=None).count()
        return Response({"parent": parent, "comment_count": comment_count})


class CommentVoteView(APIView):
    def put(self, request, uuid):
        comment = get_object_or_404(visible_comments(request.user), uuid=uuid)
        if comment.author_id == request.user.pk:
            raise PermissionDenied("Du kannst nicht über eigene Kommentare abstimmen.")
        value = request.data.get("value")
        if value not in (*CommentVote.Value.values, 0):
            return Response({"value": ["Ungültige Stimme."]}, status=status.HTTP_400_BAD_REQUEST)

        votes = CommentVote.objects.filter(user=request.user, comment=comment)
        if value:
            votes.update_or_create(user=request.user, comment=comment, defaults={"value": value})
        else:
            votes.delete()
        comment = visible_comments(request.user).get(pk=comment.pk)
        return Response({"score": compact_number(comment.score), "my_vote": comment.my_vote})


class SavedListView(generics.ListAPIView):
    serializer_class = PostSerializer
    pagination_class = SavedOrder

    def get_queryset(self):
        saves = SavedPost.objects.filter(user=self.request.user, post=OuterRef("pk"))
        folder = self.request.query_params.get("folder")
        if folder == "none":
            saves = saves.filter(folder=None)
        elif folder:
            saves = saves.filter(folder=folder)
        posts = visible_posts(self.request.user).annotate(
            saved_at=Subquery(saves.values("created_at"))
        )
        return with_details(posts.filter(saved_at__isnull=False), self.request.user)


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
