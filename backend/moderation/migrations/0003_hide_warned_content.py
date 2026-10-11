from django.db import migrations
from django.utils import timezone


def hide_warned_content(apps, schema_editor):
    Warning = apps.get_model("moderation", "Warning")
    Post = apps.get_model("posts", "Post")
    Comment = apps.get_model("posts", "Comment")
    now = timezone.now()
    Post.objects.filter(pk__in=Warning.objects.values("post"), hidden_at=None).update(hidden_at=now)
    ids = list(Warning.objects.exclude(comment=None).values_list("comment", flat=True))
    while ids:
        Comment.objects.filter(pk__in=ids).update(hidden_at=now)
        ids = list(
            Comment.objects.filter(parent__in=ids, hidden_at=None).values_list("pk", flat=True)
        )


class Migration(migrations.Migration):

    dependencies = [
        ("moderation", "0002_one_warning_per_target"),
        ("posts", "0008_hidden_content"),
    ]

    operations = [
        migrations.RunPython(hide_warned_content, migrations.RunPython.noop),
    ]
