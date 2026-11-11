from django.db.models import Q

from swissfy.posts.models import Comment, Post

from .models import Warning


def moderation_context(request):
    return {"request": request, "moderation": True}


class ReportGroup:
    def __init__(self, group, posts, comments, summaries, warned):
        self.report_count = group["report_count"]
        self.post = posts.get(group["post"])
        self.comment = comments.get(group["comment"])
        self.summary = summaries.get(self.comment.post_id) if self.comment else None
        self.warned = (group["post"], group["comment"]) in warned

    @property
    def kind(self):
        return "post" if self.post else "comment"


def load_reported(model, ids, viewer):
    return model.objects.filter(pk__in=[pk for pk in ids if pk]).with_details(viewer).in_bulk()


def report_groups(page, viewer):
    posts = load_reported(Post, [group["post"] for group in page], viewer)
    comments = load_reported(Comment, [group["comment"] for group in page], viewer)
    summaries = load_reported(Post, [comment.post_id for comment in comments.values()], viewer)
    warnings = Warning.objects.filter(Q(post__in=posts) | Q(comment__in=comments))
    warned = {(warning.post_id, warning.comment_id) for warning in warnings}
    return [ReportGroup(group, posts, comments, summaries, warned) for group in page]


class ReportedContent:
    def __init__(self, group):
        self.group = group
        self.report_count = group["report_count"]
        self.open_count = group["open_count"]

    @property
    def is_post(self):
        return bool(self.group["post"])

    @property
    def kind(self):
        return "Feed" if self.is_post else "Kommentar"

    @property
    def text(self):
        return self.group["post__text"] if self.is_post else self.group["comment__text"]

    @property
    def link(self):
        if self.is_post:
            return f"/moderation/posts/{self.group['post__uuid']}"
        return f"/moderation/comments/{self.group['comment__uuid']}"
