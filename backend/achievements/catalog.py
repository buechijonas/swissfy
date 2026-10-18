from dataclasses import dataclass
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, F, Max, Min, Q
from django.utils import timezone

from chats.models import ChatRequest
from posts.models import Comment, CommentVote, Hashtag, Like, Post, SavedPost
from social.models import Follow, Friendship

from .eggs import ANY_PATTERN, EGGS, PATTERNS
from .models import Unlock
from .themes import THEMES

User = get_user_model()

OG_ACCOUNTS = 10
PIONEER_ACCOUNTS = 100
PROFILE_FIELDS = ["avatar", "birthdate"]
USER_FIELDS = ["first_name", "last_name"]


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
    profile = getattr(user, "profile", None)
    return (
        profile is not None
        and all(getattr(profile, field) for field in PROFILE_FIELDS)
        and all(getattr(user, field) for field in USER_FIELDS)
    )


@dataclass(frozen=True)
class Achievement:
    key: str
    title: object
    description: str
    count: object
    reached: object = None
    base: int = 1
    tiered: bool = True
    bonus: bool = False


ACHIEVEMENTS = [
    Achievement(
        "og",
        "OG",
        "Gehöre zu den ersten {n} Accounts auf Swissfy.",
        lambda user: account_rank(user) < OG_ACCOUNTS,
        reached=joined,
        base=OG_ACCOUNTS,
        tiered=False,
        bonus=True,
    ),
    Achievement(
        "pioneer",
        "Rütlischwur",
        "Gehöre zu den ersten {n} Accounts auf Swissfy.",
        lambda user: account_rank(user) < PIONEER_ACCOUNTS,
        reached=joined,
        base=PIONEER_ACCOUNTS,
        tiered=False,
    ),
    Achievement(
        "open_book",
        "Charakter erstellt",
        "Hinterlege in govex Vorname, Nachname, Geburtsdatum und einen Avatar.",
        profile_complete,
        tiered=False,
    ),
    Achievement(
        "veteran",
        (
            "Tutorial abgeschlossen",
            "Willkommen in Silent Hill",
            "Stammgast",
            "Inventar",
            "Urgestein",
            "Gandalf der Graue",
            "Meister Yoda",
            "Es kann nur einen geben",
            "Marty McFly",
            "Methusalem",
        ),
        "Sei {n} Tage auf Swissfy dabei.",
        lambda user: (timezone.now() - user.date_joined).days,
        reached=days_after_joining,
        base=7,
    ),
    Achievement(
        "posts",
        (
            "Hello World",
            "Hobby-Influencer",
            "Content Creator",
            "GZSZ-Niveau",
            "Vollzeit-Influencer",
            "Liebling des Algorithmus",
        ),
        "Veröffentliche {n} Feeds.",
        **events(visible_posts),
    ),
    Achievement(
        "reels",
        (
            "VHS-Rookie",
            "Tarantino-Schüler",
            "Blockbuster",
            "Oscar-verdächtig",
            "Hollywood-Legende",
        ),
        "Lade {n} Seeds hoch.",
        **events(lambda user: visible_posts(user).exclude(video="")),
    ),
    Achievement(
        "hashtags_used",
        (
            "#NoFilter",
            "#Trendsetter",
            "#Hashtagkönig",
            "#YOLO",
            "#Hashtag-Hydra",
        ),
        "Verwende {n} verschiedene Hashtags in deinen Feeds.",
        lambda user: Hashtag.objects.filter(posts__in=visible_posts(user)).distinct().count(),
        base=3,
    ),
    Achievement(
        "likes_given",
        (
            "Daumen aus Stahl",
            "Button-Masher",
            "Like-Maschine",
            "Combo-Breaker",
            "Daumen-Olympionike",
        ),
        "Like {n} Feeds.",
        **events(lambda user: Like.objects.filter(user=user)),
        base=10,
    ),
    Achievement(
        "likes_received",
        (
            "Herzensbrecher",
            "Publikumsmagnet",
            "Bachelor-Rose",
            "Schwarm der Nation",
            "Herz-Monopol",
        ),
        "Erhalte {n} Likes auf deine Feeds.",
        **events(likes_received),
        base=10,
    ),
    Achievement(
        "superfan",
        (
            "Superfan",
            "Groupie",
            "Fanclub-Präsident",
            "Swiftie-Level",
        ),
        "Like {n} Feeds derselben Person.",
        lambda user: top_count(
            Like.objects.filter(user=user, post__hidden_at__isnull=True).exclude(post__author=user),
            "post__author",
        ),
        base=5,
    ),
    Achievement(
        "fanclub",
        (
            "Treuer Fanclub",
            "Hachiko-Treue",
            "Fankurve",
            "Beatlemania",
        ),
        "Erhalte {n} Likes von derselben Person.",
        lambda user: top_count(likes_received(user), "user"),
        base=5,
    ),
    Achievement(
        "comments_written",
        (
            "Senf-Dazugeber",
            "Stammkommentator",
            "Meinungsmacher",
            "Filibuster",
            "Kommentar-Kanone",
            "Senf-Fabrik",
        ),
        "Schreibe {n} Kommentare.",
        **events(visible_comments),
        base=5,
    ),
    Achievement(
        "comments_received",
        (
            "Gesprächsstoff",
            "Stadtgespräch",
            "Arena-Thema",
            "Breaking News",
            "Talk of the Town",
        ),
        "Erhalte {n} Kommentare auf deine Feeds.",
        **events(comments_received),
        base=5,
    ),
    Achievement(
        "crowd",
        (
            "Publikumsliebling",
            "Lagerfeuer-Erzähler",
            "Landsgemeinde",
            "Wetten, dass..?",
            "Woodstock",
        ),
        "Erhalte Kommentare von {n} verschiedenen Personen.",
        lambda user: comments_received(user).values("author").distinct().count(),
        base=5,
    ),
    Achievement(
        "sparring",
        (
            "Wortgefecht",
            "Round 1 – Fight!",
            "Rap-Battle",
            "Finish Him!",
            "Fatality",
        ),
        "Antworte {n}-mal auf Kommentare derselben Person.",
        lambda user: top_count(replies(author=user), "parent__author"),
        base=3,
    ),
    Achievement(
        "long_debate",
        (
            "Ewige Debatte",
            "Tom & Jerry",
            "Röstigraben",
            "Parlament zu zweit",
            "Krieg der Sterne",
            "Game of Thrones",
            "Kalter Krieg",
            "Hundertjähriger Krieg",
        ),
        "Diskutiere mit derselben Person in den Kommentaren über {n} Tage hinweg hin und her.",
        longest_debate,
        base=7,
    ),
    Achievement(
        "upvotes_received",
        (
            "Weise Worte",
            "Konfuzius sagt",
            "Orakel von Delphi",
            "Dumbledore-Weisheit",
            "Die Antwort ist 42",
        ),
        "Erhalte {n} Upvotes auf deine Kommentare.",
        lambda user: CommentVote.objects.filter(
            comment__in=visible_comments(user), value=CommentVote.Value.UP
        )
        .exclude(user=user)
        .count(),
        base=5,
    ),
    Achievement(
        "saves_given",
        (
            "Eichhörnchen-Modus",
            "Inventar voll",
            "Itemkiste im Save-Room",
            "Drachenhort",
        ),
        "Speichere {n} Feeds.",
        **events(lambda user: SavedPost.objects.filter(user=user)),
        base=5,
    ),
    Achievement(
        "saves_received",
        (
            "Sammlerstück",
            "Panini-Bildli",
            "Glänzendes Glurak",
            "Museumsreif",
            "Heiliger Gral",
        ),
        "Lass deine Feeds {n}-mal speichern.",
        **events(saves_received),
        base=5,
    ),
    Achievement(
        "followers",
        (
            "Kleiner Kult",
            "Lokale Berühmtheit",
            "Dorfgespräch",
            "Zombie-Horde im Schlepptau",
            "Promi",
            "Rockstar",
            "Legende",
        ),
        "Gewinne {n} Follower.",
        **events(lambda user: Follow.objects.filter(following=user)),
        base=5,
    ),
    Achievement(
        "following",
        (
            "Neugiernase",
            "Paparazzo",
            "Big Brother",
            "NSA-Praktikant",
        ),
        "Folge {n} Accounts.",
        **events(lambda user: Follow.objects.filter(follower=user)),
        base=5,
    ),
    Achievement(
        "mutual",
        (
            "Auf Gegenseitigkeit",
            "Ping & Pong",
            "Bilaterale Verträge",
            "Rebellen-Allianz",
        ),
        "Folgt euch mit {n} Accounts gegenseitig.",
        mutual_follows,
        base=3,
    ),
    Achievement(
        "friends",
        (
            "Die drei ???",
            "Friends-Clique",
            "Ocean's Eleven",
            "Ritter der Tafelrunde",
            "Bürgermeister der Herzen",
        ),
        "Schliesse {n} Freundschaften.",
        **events(lambda user: Friendship.objects.filter(user=user)),
        base=3,
    ),
    Achievement(
        "old_friends",
        (
            "Buddy-Movie",
            "Timon & Pumbaa",
            "Asterix & Obelix",
            "Frodo & Sam",
            "Rick & Daryl",
            "Ernie & Bert",
            "Han Solo & Chewbacca",
            "Bud Spencer & Terence Hill",
        ),
        "Sei seit {n} Tagen mit derselben Person befreundet.",
        longest_friendship,
        reached=days_after_oldest_friendship,
        base=30,
    ),
    Achievement(
        "hashtags_followed",
        (
            "Trendscout",
            "Pfadfinder",
            "Inspector Gadget",
            "Mulder & Scully",
        ),
        "Folge {n} Hashtags.",
        lambda user: Hashtag.objects.filter(followers=user).count(),
        base=3,
    ),
    Achievement(
        "chats",
        (
            "Eisbrecher",
            "ICQ-Uh-Oh",
            "MSN-Nostalgiker",
            "Nokia 3310",
        ),
        "Beginne {n} Chats.",
        **events(accepted_chats),
    ),
]


def theme_posts(hashtags):
    tagged = Post.objects.filter(hashtags__name__in=hashtags).values("pk")
    return lambda user: visible_posts(user).filter(pk__in=tagged)


def theme_examples(theme):
    first, second = theme["hashtags"][:2]
    return f"#{first} oder #{second}"


def theme_achievements(theme):
    examples = theme_examples(theme)
    return [
        Achievement(
            f"topic_{theme['key']}_posts",
            tuple(theme["post_titles"]),
            f"Poste {{n}}-mal mit {theme['label']}-Hashtags wie {examples}.",
            **events(theme_posts(theme["hashtags"])),
        ),
        Achievement(
            f"topic_{theme['key']}_follows",
            tuple(theme["follow_titles"]),
            f"Folge {{n}} der {theme['label']}-Hashtags wie {examples}.",
            lambda user: Hashtag.objects.filter(followers=user, name__in=theme["hashtags"]).count(),
        ),
    ]


ACHIEVEMENTS += [achievement for theme in THEMES for achievement in theme_achievements(theme)]


def titles_of(achievement):
    return (achievement.title,) if isinstance(achievement.title, str) else achievement.title


def tiers(achievement, count):
    if not achievement.tiered:
        yield achievement.title, achievement.base, bool(count), None, None
        return
    previous = 0
    for index, title in enumerate(titles_of(achievement)):
        target = achievement.base * 2**index
        yield title, target, count >= target, previous, target
        previous = target


def unlock_date(achievement, user, n):
    now = timezone.now()
    reached = achievement.reached(user, n) if achievement.reached else None
    return min(max(reached, user.date_joined), now) if reached else now


def egg_key(egg):
    return f"egg_{egg['key']}-1"


def found_eggs(user, stored):
    missing = [egg["key"] for egg in EGGS if egg_key(egg) not in stored]
    if not missing:
        return {}
    texts = [
        *visible_posts(user).filter(text__iregex=ANY_PATTERN).values_list("text", "created_at"),
        *visible_comments(user).filter(text__iregex=ANY_PATTERN).values_list("text", "created_at"),
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
                "title": egg["title"] if visible else None,
                "description": f"«{egg['quote']}» – {egg['source']}" if visible else None,
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
                    "description": achievement.description.format(n=n),
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
