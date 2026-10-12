import re

from .models import NAME_LENGTH, Hashtag

PATTERN = re.compile(rf"(?<![\w#])#(\w{{1,{NAME_LENGTH}}})")
MAX_HASHTAGS = 30


def extract(text):
    names = dict.fromkeys(name.lower() for name in PATTERN.findall(text))
    return list(names)[:MAX_HASHTAGS]


def normalize(name):
    return name.strip().lstrip("#").lower()


def tag(post):
    names = extract(post.text)
    Hashtag.objects.bulk_create([Hashtag(name=name) for name in names], ignore_conflicts=True)
    post.hashtags.set(Hashtag.objects.filter(name__in=names))
