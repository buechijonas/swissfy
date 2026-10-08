from django.core.management.base import BaseCommand

from chats.models import Message, retention_cutoff


class Command(BaseCommand):
    help = "Deletes chat messages older than CHAT_RETENTION_DAYS."

    def handle(self, *args, **options):
        deleted, _ = Message.objects.filter(created_at__lt=retention_cutoff()).delete()
        self.stdout.write(f"Deleted {deleted} objects.")
