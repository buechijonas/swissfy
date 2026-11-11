import re

from django.db import migrations

PATTERN = re.compile(r"(?<![\w#])#(\w{1,50})")


def tag_existing_posts(apps, schema_editor):
    Hashtag = apps.get_model("posts", "Hashtag")
    Post = apps.get_model("posts", "Post")
    for post in Post.objects.filter(text__contains="#"):
        names = list(dict.fromkeys(name.lower() for name in PATTERN.findall(post.text)))[:30]
        for name in names:
            Hashtag.objects.get_or_create(name=name)
        post.hashtags.set(Hashtag.objects.filter(name__in=names))


class Migration(migrations.Migration):

    dependencies = [
        ("posts", "0010_hashtags"),
    ]

    operations = [
        migrations.RunPython(tag_existing_posts, migrations.RunPython.noop),
    ]
