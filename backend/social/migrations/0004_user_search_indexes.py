from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations

FIELDS = ["username", "first_name", "last_name"]


class Migration(migrations.Migration):

    dependencies = [
        ("social", "0003_followrequest"),
    ]

    operations = [
        TrigramExtension(),
        *(
            migrations.RunSQL(
                f"CREATE INDEX IF NOT EXISTS auth_user_{field}_trgm "
                f"ON auth_user USING gin (UPPER({field}) gin_trgm_ops);",
                f"DROP INDEX IF EXISTS auth_user_{field}_trgm;",
            )
            for field in FIELDS
        ),
    ]
