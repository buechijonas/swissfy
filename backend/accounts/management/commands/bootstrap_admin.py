import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import UserProfile

User = get_user_model()

DEFAULT_USERNAME = "admin"
DEFAULT_EMAIL = "admin@swissfy.ch"
DEFAULT_PASSWORD = "admin"
ADMIN_ROLE_NAME = "Admin"


class Command(BaseCommand):
    help = (
        "Ensures an admin user with superuser rights in the 'Admin' role, for "
        "/django-admin/. Safe to re-run - if the admin user already exists, only "
        "its role/staff/superuser status is (re-)ensured, its password is left alone."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--username", default=os.environ.get("ADMIN_USERNAME", DEFAULT_USERNAME)
        )
        parser.add_argument("--email", default=os.environ.get("ADMIN_EMAIL", DEFAULT_EMAIL))
        parser.add_argument(
            "--password", default=os.environ.get("ADMIN_PASSWORD", DEFAULT_PASSWORD)
        )

    def handle(self, *args, **options):
        username = options["username"]

        with transaction.atomic():
            user, created = User.objects.get_or_create(
                username=username, defaults={"email": options["email"]}
            )
            if created:
                user.set_password(options["password"])
                self.stdout.write(
                    self.style.SUCCESS(f"Admin user '{username}' created with the given password.")
                )
            elif UserProfile.objects.filter(user=user, govex_sub__isnull=False).exists():
                self.stderr.write(
                    self.style.ERROR(
                        f"'{username}' belongs to a govex identity - not granting admin rights. "
                        "Set ADMIN_USERNAME to a name no govex user has."
                    )
                )
                return
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"User '{username}' already exists - leaving email/password untouched, "
                        "only ensuring role and superuser rights."
                    )
                )

            user.is_staff = True
            user.is_superuser = True
            user.save()
            user.groups.set([Group.objects.get(name=ADMIN_ROLE_NAME)])

        self.stdout.write(
            self.style.SUCCESS(
                f"'{username}' is now staff/superuser and assigned to the '{ADMIN_ROLE_NAME}' role."
            )
        )
