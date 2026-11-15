from dataclasses import dataclass
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, F, Max, Min, Q
from django.utils import timezone

from commons.i18n import localized
from swissfy.chats.models import ChatRequest
from swissfy.posts.models import Comment, CommentVote, Hashtag, Like, Post, SavedPost
from swissfy.social.models import Follow, Friendship

from .content import EGGS, TEXTS, THEMES
from .eggs import PATTERNS
from .models import Unlock

User = get_user_model()

OG_ACCOUNTS = 10
PIONEER_ACCOUNTS = 100


def visible_posts(user):
    return Post.objects.filter(author=user, hidden_at__isnull=True)


def visible_comments(user):
    return Comment.objects.filter(author=user, hidden_at__isnull=True)


def likes_received(user):
    return Like.objects.filter(post__in=visible_posts(user)).exclude(user=user)


def comments_received(user):
    return Comment.objects.filter(post__in=visible_posts(user), hidden_at__isnull=True).exclude(
        author=user
    )


def saves_received(user):
    return SavedPost.objects.filter(post__in=visible_posts(user)).exclude(user=user)


def accepted_chats(user):
    return ChatRequest.objects.filter(
        Q(sender=user) | Q(recipient=user), status=ChatRequest.Status.ACCEPTED
    )


def nth(queryset, n):
    dates = list(queryset.order_by("created_at").values_list("created_at", flat=True)[n - 1 : n])
    return dates[0] if dates else None


def events(queryset):
    return {
        "count": lambda user: queryset(user).count(),
        "reached": lambda user, n: nth(queryset(user), n),
    }


def joined(user, n):
    return user.date_joined


def days_after_joining(user, n):
    return user.date_joined + timedelta(days=n)


def oldest_friendship(user):
    return Friendship.objects.filter(user=user).aggregate(Min("created_at"))["created_at__min"]


def days_after_oldest_friendship(user, n):
    return oldest_friendship(user) + timedelta(days=n)


def top_count(queryset, field):
    counts = queryset.values(field).annotate(n=Count("pk")).order_by("-n")
    return counts.values_list("n", flat=True).first() or 0


def replies(**filters):
    return Comment.objects.filter(
        parent__isnull=False, hidden_at__isnull=True, parent__hidden_at__isnull=True, **filters
    ).exclude(author=F("parent__author"))


def exchanges(queryset, partner):
    return {
        row[partner]: (row["first"], row["last"])
        for row in queryset.values(partner).annotate(
            first=Min("created_at"), last=Max("created_at")
        )
    }


def longest_debate(user):
    sent = exchanges(replies(author=user), "parent__author")
    received = exchanges(replies(parent__author=user), "author")
    spans = [
        max(sent[partner][1], received[partner][1]) - min(sent[partner][0], received[partner][0])
        for partner in sent.keys() & received.keys()
    ]
    return max(spans).days if spans else 0


def mutual_follows(user):
    followers = Follow.objects.filter(following=user).values("follower")
    return Follow.objects.filter(follower=user, following__in=followers).count()


def longest_friendship(user):
    oldest = oldest_friendship(user)
    return (timezone.now() - oldest).days if oldest else 0


def account_rank(user):
    return User.objects.filter(
        Q(date_joined__lt=user.date_joined) | Q(date_joined=user.date_joined, pk__lt=user.pk)
    ).count()


def profile_complete(user):
    profile = user.profile
    return all([profile.avatar, profile.birthdate, user.first_name, user.last_name])


@dataclass(frozen=True)
class Achievement:
    key: str
    count: object
    reached: object = None
    base: int = 1
    tiered: bool = True
    bonus: bool = False

    @property
    def titles(self):
        return localized(TEXTS[self.key]["titles"])

    def description(self, n):
        return localized(TEXTS[self.key]["description"]).format(n=n)


@dataclass(frozen=True)
class ThemeAchievement(Achievement):
    theme: dict = None
    kind: str = None

    @property
    def titles(self):
        return localized(self.theme[f"{self.kind}_titles"])

    def description(self, n):
        first, second = self.theme["hashtags"][:2]
        template = localized(TEXTS[f"topic_{self.kind}s"]["description"])
        return template.format(
            n=n, label=localized(self.theme["label"]), first=first, second=second
        )


ACHIEVEMENTS = [
    Achievement(
        "og",
        lambda user: account_rank(user) < OG_ACCOUNTS,
        reached=joined,
        base=OG_ACCOUNTS,
        tiered=False,
        bonus=True,
    ),
    Achievement(
        "pioneer",
        lambda user: account_rank(user) < PIONEER_ACCOUNTS,
        reached=joined,
        base=PIONEER_ACCOUNTS,
        tiered=False,
    ),
    Achievement(
        "open_book",
        profile_complete,
        tiered=False,
    ),
    Achievement(
        "veteran",
        lambda user: (timezone.now() - user.date_joined).days,
        reached=days_after_joining,
        base=7,
    ),
    Achievement(
        "posts",
        **events(visible_posts),
    ),
    Achievement(
        "reels",
        **events(lambda user: visible_posts(user).exclude(video="")),
    ),
    Achievement(
        "hashtags_used",
        lambda user: Hashtag.objects.filter(posts__in=visible_posts(user)).distinct().count(),
        base=3,
    ),
    Achievement(
        "likes_given",
        **events(lambda user: Like.objects.filter(user=user)),
        base=10,
    ),
    Achievement(
        "likes_received",
        **events(likes_received),
        base=10,
    ),
    Achievement(
        "superfan",
        lambda user: top_count(
            Like.objects.filter(user=user, post__hidden_at__isnull=True).exclude(post__author=user),
            "post__author",
        ),
        base=5,
    ),
    Achievement(
        "fanclub",
        lambda user: top_count(likes_received(user), "user"),
        base=5,
    ),
    Achievement(
        "comments_written",
        **events(visible_comments),
        base=5,
    ),
    Achievement(
        "comments_received",
        **events(comments_received),
        base=5,
    ),
    Achievement(
        "crowd",
        lambda user: comments_received(user).values("author").distinct().count(),
        base=5,
    ),
    Achievement(
        "sparring",
        lambda user: top_count(replies(author=user), "parent__author"),
        base=3,
    ),
    Achievement(
        "long_debate",
        longest_debate,
        base=7,
    ),
    Achievement(
        "upvotes_received",
        lambda user: CommentVote.objects.filter(
            comment__in=visible_comments(user), value=CommentVote.Value.UP
        )
        .exclude(user=user)
        .count(),
        base=5,
    ),
    Achievement(
        "saves_given",
        **events(lambda user: SavedPost.objects.filter(user=user)),
        base=5,
    ),
    Achievement(
        "saves_received",
        **events(saves_received),
        base=5,
    ),
    Achievement(
        "followers",
        **events(lambda user: Follow.objects.filter(following=user)),
        base=5,
    ),
    Achievement(
        "following",
        **events(lambda user: Follow.objects.filter(follower=user)),
        base=5,
    ),
    Achievement(
        "mutual",
        mutual_follows,
        base=3,
    ),
    Achievement(
        "friends",
        **events(lambda user: Friendship.objects.filter(user=user)),
        base=3,
    ),
    Achievement(
        "old_friends",
        longest_friendship,
        reached=days_after_oldest_friendship,
        base=30,
    ),
    Achievement(
        "hashtags_followed",
        lambda user: Hashtag.objects.filter(followers=user).count(),
        base=3,
    ),
    Achievement(
        "chats",
        **events(accepted_chats),
    ),
]


def theme_posts(hashtags):
    tagged = Post.objects.filter(hashtags__name__in=hashtags).values("pk")
    return lambda user: visible_posts(user).filter(pk__in=tagged)


def theme_achievements(theme):
    return [
        ThemeAchievement(
            f"topic_{theme['key']}_posts",
            theme=theme,
            kind="post",
            **events(theme_posts(theme["hashtags"])),
        ),
        ThemeAchievement(
            f"topic_{theme['key']}_follows",
            lambda user: Hashtag.objects.filter(followers=user, name__in=theme["hashtags"]).count(),
            theme=theme,
            kind="follow",
        ),
    ]


ACHIEVEMENTS += [achievement for theme in THEMES for achievement in theme_achievements(theme)]


def tiers(achievement, count):
    if not achievement.tiered:
        yield achievement.titles[0], achievement.base, bool(count), None, None
        return
    previous = 0
    for index, title in enumerate(achievement.titles):
        target = achievement.base * 2**index
        yield title, target, count >= target, previous, target
        previous = target


def unlock_date(achievement, user, n):
    now = timezone.now()
    reached = achievement.reached(user, n) if achievement.reached else None
    return min(max(reached, user.date_joined), now) if reached else now


def egg_key(egg):
    return f"egg_{egg['key']}-1"


def egg_description(egg):
    return f"«{localized(egg['quote'])}» – {localized(egg['source'])}"


def found_eggs(user, stored):
    missing = [egg["key"] for egg in EGGS if egg_key(egg) not in stored]
    if not missing:
        return {}
    texts = [
        *visible_posts(user).values_list("text", "created_at"),
        *visible_comments(user).values_list("text", "created_at"),
    ]
    found = {}
    for text, created_at in sorted(texts, key=lambda row: row[1]):
        for key in missing:
            if key not in found and PATTERNS[key].search(text):
                found[key] = created_at
    return found


def egg_entries(user, stored, new, reveal):
    found = found_eggs(user, stored)
    results = []
    for egg in EGGS:
        key = egg_key(egg)
        if egg["key"] in found:
            stored[key] = found[egg["key"]]
            new.append(Unlock(user=user, key=key, unlocked_at=stored[key]))
        unlocked = key in stored
        visible = unlocked or reveal
        results.append(
            {
                "key": key,
                "group": f"egg_{egg['key']}",
                "level": 1,
                "title": localized(egg["title"]) if visible else None,
                "description": egg_description(egg) if visible else None,
                "unlocked": unlocked,
                "unlocked_at": stored.get(key),
                "bonus": False,
                "secret": True,
                "count": None,
                "previous": None,
                "target": None,
            }
        )
    return results


def achievements_of(user, reveal_secrets=False):
    stored = dict(Unlock.objects.filter(user=user).values_list("key", "unlocked_at"))
    results, new = [], []
    for achievement in ACHIEVEMENTS:
        count = achievement.count(user)
        for level, (title, n, earned, previous, target) in enumerate(
            tiers(achievement, count), start=1
        ):
            key = f"{achievement.key}-{level}"
            if earned and key not in stored:
                stored[key] = unlock_date(achievement, user, n)
                new.append(Unlock(user=user, key=key, unlocked_at=stored[key]))
            results.append(
                {
                    "key": key,
                    "group": achievement.key,
                    "level": level,
                    "title": title,
                    "description": achievement.description(n),
                    "unlocked": key in stored,
                    "unlocked_at": stored.get(key),
                    "bonus": achievement.bonus,
                    "secret": False,
                    "count": None if target is None else count,
                    "previous": previous,
                    "target": target,
                }
            )
    results += egg_entries(user, stored, new, reveal_secrets)
    Unlock.objects.bulk_create(new, ignore_conflicts=True)
    return results
