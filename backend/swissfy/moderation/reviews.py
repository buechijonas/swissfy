from django.db.models import Q

from swissfy.accounts.roles import is_moderator, outranks
from swissfy.posts.models import Comment, Post
from swissfy.posts.serializers import CommentModelSerializer, PostModelSerializer

from .models import Reason, Report, Suspension, Warning
from .serializers import SuspensionModelSerializer, WarningModelSerializer


def moderation_context(request):
    return {"request": request, "moderation": True}


class ReportQueuePage:
    def __init__(self, page, request):
        self.page = page
        self.context = moderation_context(request)
        viewer = request.user
        self.posts = self.load(Post, "post", viewer)
        self.comments = self.load(Comment, "comment", viewer)
        self.summaries = (
            Post.objects.filter(pk__in=[comment.post_id for comment in self.comments.values()])
            .with_details(viewer)
            .in_bulk()
        )
        warnings = Warning.objects.filter(Q(post__in=self.posts) | Q(comment__in=self.comments))
        self.warned = {(warning.post_id, warning.comment_id) for warning in warnings}

    def load(self, model, field, viewer):
        ids = [item[field] for item in self.page if item[field]]
        return model.objects.filter(pk__in=ids).with_details(viewer).in_bulk()

    def results(self):
        return [self.result(item) for item in self.page]

    def result(self, item):
        summary = {
            "report_count": item["report_count"],
            "warned": (item["post"], item["comment"]) in self.warned,
        }
        if item["post"]:
            return {"type": "post", **summary, "post": self.post(self.posts[item["post"]])}
        comment = self.comments[item["comment"]]
        return {
            "type": "comment",
            **summary,
            "comment": CommentModelSerializer.read(comment, context=self.context).data,
            "post": PostModelSerializer.summary(
                self.summaries[comment.post_id], context=self.context
            ).data,
        }

    def post(self, post):
        return PostModelSerializer.read(post, context=self.context).data


def moderation_details(viewer, target, **lookup):
    warnings = Warning.objects.filter(**lookup)
    return {
        "report_count": Report.objects.open().filter(**lookup).count(),
        "can_warn": not warnings.exists() and not outranks(target.author, viewer),
        "reasons": Reason.options(),
        "warnings": WarningModelSerializer.read(warnings, many=True).data,
    }


def status_events(user, moderation):
    warnings = Warning.objects.filter(user=user).select_related("post", "comment")
    suspensions = Suspension.objects.filter(user=user).select_related("warning")
    events = [
        *WarningModelSerializer.read(warnings, many=True, context={"moderation": moderation}).data,
        *SuspensionModelSerializer.read(suspensions, many=True).data,
    ]
    return sorted(
        events, key=lambda event: (event["caused_at"], event["type"] == "suspension"), reverse=True
    )


def reported_content(user):
    return [reported_item(group) for group in Report.objects.about(user)]


def reported_item(group):
    if group["post"]:
        kind, text, link = "Feed", group["post__text"], f"/moderation/posts/{group['post__uuid']}"
    else:
        kind, text = "Kommentar", group["comment__text"]
        link = f"/moderation/comments/{group['comment__uuid']}"
    return {
        "type": kind,
        "text": text,
        "report_count": group["report_count"],
        "open_count": group["open_count"],
        "link": link,
    }


def status_of(user, viewer):
    moderating = is_moderator(viewer)
    return {
        "events": status_events(user, moderating),
        "reports": reported_content(user) if moderating else None,
    }
