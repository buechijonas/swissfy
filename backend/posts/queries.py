from django.db.models import Count, Exists, IntegerField, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce, TruncDate

from accounts.models import UserProfile
from social.models import Follow, Friendship

from .models import Comment, CommentVote, ContactGroup, Like, Post, SavedPost


def visible_posts(viewer):
    Audience = Post.Visibility
    Profile = UserProfile.Visibility
    profile_visible = (
        Q(author__profile__isnull=True)
        | Q(author__profile__profile_visibility=Profile.PUBLIC)
        | Q(author__profile__profile_visibility=Profile.FOLLOWERS, viewer_follows=True)
        | Q(viewer_is_friend=True)
    )
    audience = (
        Q(visibility=Audience.PUBLIC)
        | Q(visibility=Audience.FOLLOWERS, viewer_follows=True)
        | Q(visibility=Audience.FRIENDS, viewer_is_friend=True)
        | Q(visibility=Audience.GROUPS, viewer_in_group=True)
    )
    return (
        Post.objects.filter(author__is_active=True)
        .annotate(
            viewer_follows=Exists(
                Follow.objects.filter(follower=viewer, following=OuterRef("author"))
            ),
            viewer_is_friend=Exists(
                Friendship.objects.filter(user=viewer, friend=OuterRef("author"))
            ),
            viewer_in_group=Exists(
                ContactGroup.objects.filter(posts=OuterRef("pk"), members=viewer)
            ),
        )
        .filter(Q(author=viewer) | (profile_visible & audience))
    )


def feed(viewer):
    return (
        visible_posts(viewer)
        .filter(Q(viewer_follows=True) | Q(viewer_is_friend=True))
        .annotate(day=TruncDate("created_at"))
    )


def count_of(queryset, field="post"):
    counts = (
        queryset.filter(**{field: OuterRef("pk")})
        .order_by()
        .values(field)
        .annotate(count=Count("pk"))
        .values("count")
    )
    return Coalesce(Subquery(counts, output_field=IntegerField()), Value(0))


def with_details(posts, viewer):
    saves = SavedPost.objects.filter(user=viewer, post=OuterRef("pk"))
    return (
        posts.select_related("author__profile")
        .prefetch_related("groups", "images")
        .annotate(
            like_count=count_of(Like.objects.all()),
            comment_count=count_of(Comment.objects.filter(parent=None)),
            liked=Exists(Like.objects.filter(user=viewer, post=OuterRef("pk"))),
            saved=Exists(saves),
            saved_folder=Subquery(saves.values("folder")),
        )
    )


def comment_details(comments, viewer):
    votes = CommentVote.objects.filter(comment=OuterRef("pk"))
    score = votes.order_by().values("comment").annotate(score=Sum("value")).values("score")
    return comments.select_related("post", "author__profile", "parent__author").annotate(
        reply_count=count_of(Comment.objects.all(), "parent"),
        score=Coalesce(Subquery(score, output_field=IntegerField()), Value(0)),
        my_vote=Coalesce(Subquery(votes.filter(user=viewer).values("value")), Value(0)),
    )


def attach_latest_replies(comments, viewer):
    latest = comment_details(
        Comment.objects.filter(parent__in=comments).order_by("parent", "-id").distinct("parent"),
        viewer,
    )
    replies = {reply.parent_id: reply for reply in latest}
    for comment in comments:
        comment.latest_reply = replies.get(comment.pk)
    return comments
