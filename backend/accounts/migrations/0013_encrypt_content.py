from django.db import migrations

import commons.models
from commons.backfill import encrypt_rows


def encrypt_content(apps, schema_editor):
    encrypt_rows(
        apps.get_model("accounts", "UserProfile"),
        texts=["biography"],
        files=["public_picture", "private_picture"],
    )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0012_profile_for_every_user"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="biography",
            field=commons.models.EncryptedTextField(
                blank=True, max_length=500, verbose_name="Biografie"
            ),
        ),
        migrations.RunPython(encrypt_content, migrations.RunPython.noop),
    ]
