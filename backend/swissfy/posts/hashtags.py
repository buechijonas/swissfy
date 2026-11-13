import re

from .models import NAME_LENGTH, Hashtag

PATTERN = re.compile(rf"(?<![\w#])#(\w{{1,{NAME_LENGTH}}})")
MAX_HASHTAGS = 30


def extract(text):
    names = dict.fromkeys(name.lower() for name in PATTERN.findall(text))
    return list(names)[:MAX_HASHTAGS]


def split(text):
    parts = []
    start = 0
    for match in PATTERN.finditer(text):
        if match.start() > start:
            parts.append({"start": start, "text": text[start : match.start()], "hashtag": None})
        parts.append({"start": match.start(), "text": match[0], "hashtag": match[1].lower()})
        start = match.end()
    if start < len(text):
        parts.append({"start": start, "text": text[start:], "hashtag": None})
    return parts


def normalize(name):
    return name.strip().lstrip("#").lower()


def tag(post):
    names = extract(post.text)
    Hashtag.objects.bulk_create([Hashtag(name=name) for name in names], ignore_conflicts=True)
    post.hashtags.set(Hashtag.objects.filter(name__in=names))
