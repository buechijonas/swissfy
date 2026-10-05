from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from accounts.models import UserProfile, get_or_create_profile

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Links an existing swissfy user to a govex identity, so logging in "
        "via govex lands in that account (keeping its role, avatar, consent). "
        "The govex sub is the user's UUID in the authentik admin UI "
        "(Directory > Users)."
    )

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("govex_sub")

    def handle(self, *args, **options):
        user = User.objects.filter(username=options["username"]).first()
        if user is None:
            raise CommandError(f"User '{options['username']}' not found.")

        govex_sub = options["govex_sub"]
        taken = UserProfile.objects.filter(govex_sub=govex_sub).exclude(user=user).first()
        if taken:
            raise CommandError(f"govex identity {govex_sub} is already linked to '{taken.user}'.")

        profile = get_or_create_profile(user)
        profile.govex_sub = govex_sub
        profile.save(update_fields=["govex_sub"])
        user.set_unusable_password()
        user.save(update_fields=["password"])
        self.stdout.write(
            self.style.SUCCESS(f"'{user}' is now linked to govex identity {govex_sub}.")
        )
