import re
from datetime import timedelta
from urllib.parse import urlencode
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Q, Subquery
from django.http import FileResponse, HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, Throttled
from rest_framework.pagination import CursorPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.roles import is_moderator
from main.numbers import compact_number
from main.parsers import JSONParser
from moderation.sanctions import ensure_not_suspended
from notifications.models import Notification
from notifications.notify import notify, withdraw
from social.serializers import can_view_profile

from . import hashtags
from .models import (
    Comment,
    CommentVote,
    ContactGroup,
    Hashtag,
    Like,
    Post,
    PostCreation,
    PostImage,
    SavedFolder,
    SavedPost,
)
from .queries import (
    attach_latest_replies,
    comment_details,
    comment_visibility,
    feed,
    reported_comments,
    unavailable,
    visible_posts,
    with_details,
)
from .serializers import (
    CommentSerializer,
    ContactGroupSerializer,
    HashtagSerializer,
    PostCreateSerializer,
    PostSerializer,
    PostSummarySerializer,
    SavedFolderSerializer,
)

User = get_user_model()

POSTS_PER_DAY = 10
BYTE_RANGE = re.compile(r"bytes=(\d*)-(\d*)$")
CHUNK_SIZE = 64 * 1024


class NewestFirst(CursorPagination):
    page_size = 25
    ordering = "-id"


class FeedOrder(NewestFirst):
    ordering = ("-day", "-viewer_is_friend", "-id")


class SavedOrder(NewestFirst):
    ordering = "-saved_at"


class OldestFirst(CursorPagination):
    page_size = 50
    ordering = "created_at"


def starting_from(posts, request):
    try:
        start = UUID(request.query_params.get("from", ""))
    except ValueError:
        return posts
    return posts.filter(pk__lte=Subquery(Post.objects.filter(uuid=start).values("pk")))


def by_media(posts, request):
    if request.query_params.get("images"):
        posts = posts.exclude(thumbnail="").filter(video_status="")
    if request.query_params.get("videos"):
        posts = posts.filter(video_status=Post.VideoStatus.READY)
    return starting_from(posts, request)


def hashtags_for(viewer):
    followers = Hashtag.followers.through.objects.filter(hashtag=OuterRef("pk"), user=viewer)
    visible = visible_posts(viewer).values("pk")
    return Hashtag.objects.annotate(
        post_count=Count("posts", filter=Q(posts__in=visible), distinct=True),
        following=Exists(followers),
    )


def visible_post(request, uuid):
    return get_object_or_404(visible_posts(request.user), uuid=uuid)


def remaining_posts(user):
    creations = PostCreation.objects.filter(author=user)
    recent = creations.filter(created_at__gte=timezone.now() - timedelta(days=1))
    return max(0, POSTS_PER_DAY - recent.count())


def check_quota(user):
    if not remaining_posts(user):
        raise Throttled(detail=f"Du kannst höchstens {POSTS_PER_DAY} Posts pro Tag erstellen.")


def notify_comment(comment):
    notify(
        comment.post.author,
        Notification.Kind.COMMENT,
        actor=comment.author,
        post=comment.post,
        comment=comment,
    )


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


class FeedView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    pagination_class = FeedOrder
    parser_classes = [MultiPartParser, JSONParser]

    def get_queryset(self):
        return with_details(feed(self.request.user), self.request.user)

    def create(self, request, *args, **kwargs):
        ensure_not_suspended(request.user)
        check_quota(request.user)
        serializer = PostCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            User.objects.select_for_update().get(pk=request.user.pk)
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
        return with_details(by_media(posts, self.request), self.request.user)


class ReelFeedView(generics.ListAPIView):
    serializer_class = PostSerializer
    pagination_class = NewestFirst

    def get_queryset(self):
        reels = feed(self.request.user).filter(video_status=Post.VideoStatus.READY)
        return with_details(starting_from(reels, self.request), self.request.user)


class HashtagSearchView(generics.ListAPIView):
    serializer_class = HashtagSerializer
    pagination_class = None

    def get_queryset(self):
        query = hashtags.normalize(self.request.query_params.get("q", ""))
        if not query:
            return Hashtag.objects.none()
        tags = hashtags_for(self.request.user).filter(name__startswith=query, post_count__gt=0)
        return tags.order_by("-post_count", "name")[:20]


class HashtagDetailView(generics.RetrieveAPIView):
    serializer_class = HashtagSerializer

    def get_object(self):
        name = hashtags.normalize(self.kwargs["name"])
        return get_object_or_404(hashtags_for(self.request.user), name=name)


class HashtagFollowView(HashtagDetailView):
    def put(self, request, name):
        self.get_object().followers.add(request.user)
        return self.retrieve(request)

    def delete(self, request, name):
        self.get_object().followers.remove(request.user)
        return self.retrieve(request)


class HashtagPostListView(generics.ListAPIView):
    serializer_class = PostSerializer
    pagination_class = NewestFirst

    def get_queryset(self):
        name = hashtags.normalize(self.kwargs["name"])
        posts = visible_posts(self.request.user).filter(hashtags__name=name)
        return with_details(by_media(posts, self.request), self.request.user)


class ActivityView(APIView):
    def get(self, request, username):
        viewer = request.user
        posts = visible_posts(viewer).filter(author__username=username)
        on_visible_post = Q(post__in=visible_posts(viewer).values("pk")) | Q(author=viewer)
        if is_moderator(viewer):
            on_visible_post |= reported_comments()
        comments = Comment.objects.filter(
            comment_visibility(viewer), on_visible_post, author__username=username
        )
        author = User.objects.filter(username=username).select_related("profile").first()
        if author and not can_view_profile(viewer, author):
            comments = (
                comments.filter(reported_comments()) if is_moderator(viewer) else comments.none()
            )
        comments = comment_details(comments, viewer)
        before = parse_datetime(request.query_params.get("before", ""))
        if before:
            posts = posts.filter(created_at__lt=before)
            comments = comments.filter(created_at__lt=before)

        page_size = NewestFirst.page_size
        posts = list(with_details(posts, viewer).order_by("-created_at")[:page_size])
        comments = list(comments.order_by("-created_at")[:page_size])
        context_posts = Post.objects.all() if is_moderator(viewer) else visible_posts(viewer)
        post_ids = {comment.post_id for comment in comments}
        visible = with_details(context_posts, viewer).in_bulk(post_ids)
        commented = Post.objects.select_related("author").in_bulk(post_ids)
        items = sorted(posts + comments, key=lambda item: item.created_at, reverse=True)
        items = items[:page_size]

        context = {"request": request}
        results = [
            (
                {
                    "type": "comment",
                    **CommentSerializer(item, context=context).data,
                    "post": post_summary(commented[item.post_id], visible, context),
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


class LikeView(APIView):
    def post(self, request, uuid):
        post = visible_post(request, uuid)
        _, created = Like.objects.get_or_create(user=request.user, post=post)
        if created:
            notify(post.author, Notification.Kind.LIKE, actor=request.user, post=post)
        return self.state(post, True)

    def delete(self, request, uuid):
        post = visible_post(request, uuid)
        Like.objects.filter(user=request.user, post=post).delete()
        withdraw(post.author, Notification.Kind.LIKE, request.user, post=post)
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
    on_visible_post = Q(post__in=visible_posts(viewer)) | Q(author=viewer)
    comments = Comment.objects.filter(comment_visibility(viewer), on_visible_post)
    return comment_details(comments, viewer)


def post_summary(post, visible, context):
    if post.pk in visible:
        return PostSummarySerializer(visible[post.pk], context=context).data
    return unavailable(post, "Post")


class CommentListView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    pagination_class = OldestFirst

    def get_post(self):
        return visible_post(self.request, self.kwargs["uuid"])

    def comment_visibility(self):
        return comment_visibility(self.request.user)

    def get_queryset(self):
        comments = self.get_post().comments.filter(self.comment_visibility(), parent=None)
        return comment_details(comments, self.request.user)

    def list(self, request, *args, **kwargs):
        page = attach_latest_replies(
            self.paginate_queryset(self.get_queryset()),
            request.user,
            self.comment_visibility(),
        )
        return self.get_paginated_response(self.get_serializer(page, many=True).data)

    def create(self, request, *args, **kwargs):
        ensure_not_suspended(request.user)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        comment = serializer.save(
            post=visible_post(self.request, self.kwargs["uuid"]), author=self.request.user
        )
        notify_comment(comment)


class CommentReplyListView(CommentListView):
    def parent(self):
        return get_object_or_404(visible_comments(self.request.user), uuid=self.kwargs["uuid"])

    def get_queryset(self):
        replies = self.parent().replies.filter(self.comment_visibility())
        return comment_details(replies, self.request.user)

    def perform_create(self, serializer):
        parent = self.parent()
        if not visible_posts(self.request.user).filter(pk=parent.post_id).exists():
            raise PermissionDenied("Dieser Post ist nicht mehr verfügbar.")
        comment = serializer.save(post=parent.post, parent=parent, author=self.request.user)
        notify_comment(comment)


class CommentDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = CommentSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return visible_comments(self.request.user)

    def get_posts(self):
        return with_details(visible_posts(self.request.user), self.request.user)

    def retrieve(self, request, *args, **kwargs):
        comment = self.get_object()
        chain = []
        parent_id = comment.parent_id
        while parent_id:
            chain.append(parent_id)
            parent_id = Comment.objects.values_list("parent_id", flat=True).get(pk=parent_id)
        ancestors = self.get_queryset().in_bulk(chain)
        hidden_ancestors = Comment.objects.select_related("author").in_bulk(chain)
        context = self.get_serializer_context()
        visible = self.get_posts().in_bulk([comment.post_id])
        return Response(
            {
                **self.get_serializer(comment).data,
                "ancestors": [
                    (
                        self.get_serializer(ancestors[pk]).data
                        if pk in ancestors
                        else unavailable(hidden_ancestors[pk], "Kommentar")
                    )
                    for pk in reversed(chain)
                ],
                "post": post_summary(comment.post, visible, context),
            }
        )

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author_id != request.user.pk:
            raise PermissionDenied("Du kannst nur eigene Kommentare löschen.")
        comment.delete()

        parent = self.get_queryset().filter(pk=comment.parent_id).first()
        if parent:
            parent = attach_latest_replies(
                [parent], request.user, comment_visibility(request.user)
            )[0]
            parent = self.get_serializer(parent).data
        comment_count = Comment.objects.filter(
            comment_visibility(request.user), post=comment.post_id, parent=None
        ).count()
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
        saves = SavedPost.objects.filter(user=self.request.user)
        folder = self.request.query_params.get("folder")
        if folder == "none":
            saves = saves.filter(folder=None)
        elif folder and folder.isdigit():
            saves = saves.filter(folder=folder)
        elif folder:
            saves = saves.none()
        posts = (
            visible_posts(self.request.user)
            .filter(pk__in=saves.values("post"))
            .annotate(saved_at=Subquery(saves.filter(post=OuterRef("pk")).values("created_at")))
        )
        return with_details(posts, self.request.user)


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
