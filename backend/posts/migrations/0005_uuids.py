from uuid import uuid4

from django.db import migrations, models


def fill_uuids(apps, schema_editor):
    for name in ("Post", "Comment"):
        model = apps.get_model("posts", name)
        for item in model.objects.all():
            item.uuid = uuid4()
            item.save(update_fields=["uuid"])


class Migration(migrations.Migration):

    dependencies = [
        ("posts", "0004_comment_parent"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="uuid",
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name="comment",
            name="uuid",
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.RunPython(fill_uuids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="post",
            name="uuid",
            field=models.UUIDField(default=uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name="comment",
            name="uuid",
            field=models.UUIDField(default=uuid4, editable=False, unique=True),
        ),
    ]
