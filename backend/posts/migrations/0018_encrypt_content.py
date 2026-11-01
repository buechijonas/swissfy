from django.db import migrations

import commons.models
from commons.backfill import encrypt_rows


def encrypt_content(apps, schema_editor):
    encrypt_rows(
        apps.get_model("posts", "Post"),
        texts=["text"],
        files=["thumbnail", "video", "video_upload"],
    )
    encrypt_rows(apps.get_model("posts", "PostImage"), files=["file"])
    encrypt_rows(apps.get_model("posts", "Story"), texts=["text"], files=["image"])
    encrypt_rows(apps.get_model("posts", "Comment"), texts=["text"])


class Migration(migrations.Migration):
    dependencies = [
        ("posts", "0017_image_dimensions"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comment",
            name="text",
            field=commons.models.EncryptedTextField(max_length=500),
        ),
        migrations.AlterField(
            model_name="post",
            name="text",
            field=commons.models.EncryptedTextField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name="story",
            name="text",
            field=commons.models.EncryptedTextField(blank=True, max_length=200),
        ),
        migrations.RunPython(encrypt_content, migrations.RunPython.noop),
    ]
