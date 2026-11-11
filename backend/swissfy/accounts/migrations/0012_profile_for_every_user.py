from django.conf import settings
from django.db import migrations


def create_missing_profiles(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    UserProfile = apps.get_model("accounts", "UserProfile")
    UserProfile.objects.bulk_create(
        UserProfile(user=user) for user in User.objects.filter(profile__isnull=True)
    )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0011_device_tokens"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [migrations.RunPython(create_missing_profiles, migrations.RunPython.noop)]
