from django.db.models import Count, Exists, IntegerField, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce, TruncDate

from accounts.models import UserProfile
from accounts.roles import is_admin, is_moderator
from moderation.sanctions import is_suspended, suspended_users
from social.models import Follow, Friendship

from .models import Comment, CommentVote, ContactGroup, Like, Post, SavedPost

NOT_HIDDEN = Q(hidden_at__isnull=True)


def reported_comments():
    return Q(pk__in=Comment.objects.filter(reports__isnull=False).values("pk"))


def by_suspended_author():
    return Q(author__in=suspended_users())


def comment_visibility(viewer):
    if is_admin(viewer):
        return Q()
    visible = NOT_HIDDEN & (~by_suspended_author() | Q(author=viewer))
    return visible | reported_comments() if is_moderator(viewer) else visible


def unavailable(item, label):
    if item.hidden_at:
        reason = f"Dieser {label} wurde gesperrt."
    elif is_suspended(item.author):
        reason = "Der User wurde gesperrt und ist nicht sichtbar."
    else:
        reason = f"Dieser {label} ist nicht sichtbar."
    return {"id": str(item.uuid), "unavailable": reason}


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
    posts = Post.objects.filter(author__is_active=True).annotate(
        viewer_follows=Exists(Follow.objects.filter(follower=viewer, following=OuterRef("author"))),
        viewer_is_friend=Exists(Friendship.objects.filter(user=viewer, friend=OuterRef("author"))),
        viewer_in_group=Exists(ContactGroup.objects.filter(posts=OuterRef("pk"), members=viewer)),
    )
    unfinished_video = Q(video_status__in=[Post.VideoStatus.PROCESSING, Post.VideoStatus.FAILED])
    posts = posts.filter(~unfinished_video | Q(author=viewer))
    if is_admin(viewer):
        return posts
    global_post = Q(visibility=Audience.GLOBAL)
    visible = NOT_HIDDEN & (
        Q(author=viewer) | (((profile_visible & audience) | global_post) & ~by_suspended_author())
    )
    if is_moderator(viewer):
        visible |= Q(pk__in=Post.objects.filter(reports__isnull=False).values("pk"))
    return posts.filter(visible)


def with_followed_hashtag(viewer):
    return Post.objects.filter(hashtags__followers=viewer).values("pk")


def feed(viewer):
    followed = Follow.objects.filter(follower=viewer).values("following")
    friends = Friendship.objects.filter(user=viewer).values("friend")
    return (
        visible_posts(viewer)
        .filter(
            Q(author=viewer)
            | Q(author__in=followed.union(friends))
            | Q(pk__in=with_followed_hashtag(viewer))
            | Q(visibility=Post.Visibility.GLOBAL)
        )
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
        .prefetch_related("groups", "images", "author__groups")
        .annotate(
            reported=Exists(Post.objects.filter(pk=OuterRef("pk"), reports__reporter=viewer)),
            like_count=count_of(Like.objects.all()),
            comment_count=count_of(Comment.objects.filter(comment_visibility(viewer), parent=None)),
            liked=Exists(Like.objects.filter(user=viewer, post=OuterRef("pk"))),
            saved=Exists(saves),
            saved_folder=Subquery(saves.values("folder")),
        )
    )


def comment_details(comments, viewer):
    votes = CommentVote.objects.filter(comment=OuterRef("pk"))
    score = votes.order_by().values("comment").annotate(score=Sum("value")).values("score")
    reports = Comment.objects.filter(pk=OuterRef("pk"), reports__reporter=viewer)
    return (
        comments.select_related("post", "author__profile", "parent__author")
        .prefetch_related("author__groups")
        .annotate(
            reported=Exists(reports),
            reply_count=count_of(Comment.objects.filter(comment_visibility(viewer)), "parent"),
            score=Coalesce(Subquery(score, output_field=IntegerField()), Value(0)),
            my_vote=Coalesce(Subquery(votes.filter(user=viewer).values("value")), Value(0)),
        )
    )


def attach_latest_replies(comments, viewer, visible=Q()):
    replies = Comment.objects.filter(visible, parent__in=comments)
    latest = comment_details(replies.order_by("parent", "-id").distinct("parent"), viewer)
    by_parent = {reply.parent_id: reply for reply in latest}
    for comment in comments:
        comment.latest_reply = by_parent.get(comment.pk)
    return comments
