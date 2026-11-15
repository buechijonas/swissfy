import django.db.models.deletion
from django.db import migrations, models

import commons.models
from commons.backfill import encrypt_rows


def encrypt_wrapped_keys(apps, schema_editor):
    encrypt_rows(apps.get_model("chats", "ChatKey"), texts=["wrapped_private_key"])


class Migration(migrations.Migration):

    dependencies = [
        ("chats", "0005_archivedchat"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatkey",
            name="failed_unlocks",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="chatkey",
            name="pin_verifier",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="chatkey",
            name="unlock_blocked_until",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="message",
            name="sender_key",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="chats.chatkey",
            ),
        ),
        migrations.AddField(
            model_name="message",
            name="signature",
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AlterField(
            model_name="chatkey",
            name="wrapped_private_key",
            field=commons.models.EncryptedTextField(blank=True),
        ),
        migrations.RunPython(encrypt_wrapped_keys, migrations.RunPython.noop),
    ]
