import django.db.models.deletion
from django.db import migrations, models


def delete_cover_files(apps, schema_editor):
    for album in apps.get_model("posts", "Album").objects.exclude(cover=""):
        album.cover.delete(save=False)


class Migration(migrations.Migration):

    dependencies = [
        ("posts", "0015_albums"),
    ]

    operations = [
        migrations.RunPython(delete_cover_files, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="album",
            name="cover",
        ),
        migrations.AddField(
            model_name="album",
            name="cover",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="posts.albumentry",
            ),
        ),
    ]
