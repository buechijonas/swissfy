from django.core.management.base import BaseCommand

from posts.models import Story, story_cutoff


class Command(BaseCommand):
    help = "Deletes stories older than STORY_LIFETIME together with their images."

    def handle(self, *args, **options):
        deleted, _ = Story.objects.filter(created_at__lt=story_cutoff()).delete()
        self.stdout.write(f"Deleted {deleted} objects.")
