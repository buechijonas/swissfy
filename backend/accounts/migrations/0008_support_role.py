from django.db import migrations


def add_support_role(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    User = apps.get_model("auth", "User")
    Group.objects.get_or_create(name="Support")
    admin = Group.objects.get(name="Admin")
    for user in User.objects.filter(is_superuser=True):
        user.groups.set([admin])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_userprofile_show_birthdate"),
    ]

    operations = [
        migrations.RunPython(add_support_role, migrations.RunPython.noop),
    ]
