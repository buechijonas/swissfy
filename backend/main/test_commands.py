from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from swissfy.accounts.roles import Role, role_of
from swissfy.chats.models import ChatRequest, Message
from swissfy.moderation.models import Report, Suspension, Warning
from swissfy.notifications.models import Notification

User = get_user_model()


def run(command, *args):
    call_command(command, *args, stdout=StringIO(), stderr=StringIO())


class SeedDemoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        run("seed_demo")
        cls.demo = User.objects.filter(username__startswith="demo_")

    def assert_served(self, url):
        admin = next(user for user in self.demo if role_of(user) == Role.ADMIN)
        self.client.force_login(admin)
        self.assertEqual(self.client.get(url).status_code, 200)

    @property
    def member(self):
        return self.demo.filter(is_active=True).order_by("pk").last().username

    def test_creates_demo_users(self):
        self.assertTrue(self.demo.exists())

    def test_creates_chats(self):
        self.assertTrue(ChatRequest.objects.exists())
        self.assertTrue(Message.objects.exists())

    def test_creates_reports_and_sanctions(self):
        self.assertTrue(Report.objects.exists())
        self.assertTrue(Warning.objects.exists())
        self.assertTrue(Suspension.objects.exists())

    def test_creates_notifications(self):
        self.assertTrue(Notification.objects.exists())

    def test_is_repeatable(self):
        count = self.demo.count()
        run("seed_demo")
        self.assertEqual(User.objects.filter(username__startswith="demo_").count(), count)

    def test_serves_feed(self):
        self.assert_served("/api/posts/")

    def test_serves_profile_list(self):
        self.assert_served("/api/social/profiles/")

    def test_serves_profile(self):
        self.assert_served(f"/api/social/profiles/{self.member}/")

    def test_serves_followers(self):
        self.assert_served(f"/api/social/profiles/{self.member}/followers/")

    def test_serves_moderation_status(self):
        self.assert_served(f"/api/social/profiles/{self.member}/status/")

    def test_serves_achievements(self):
        self.assert_served(f"/api/social/profiles/{self.member}/achievements/")

    def test_serves_conversations(self):
        self.assert_served("/api/chats/conversations/")

    def test_serves_chat_requests(self):
        self.assert_served("/api/chats/requests/")

    def test_serves_notifications(self):
        self.assert_served("/api/notifications/")

    def test_serves_open_reports(self):
        self.assert_served("/api/moderation/reports/")

    def test_serves_resolved_reports(self):
        self.assert_served("/api/moderation/reports/?status=resolved")

    def test_serves_administration(self):
        self.assert_served("/api/administration/users/")


class CleanupCommandTests(TestCase):
    def test_delete_old_messages_keeps_recent_ones(self):
        anna = User.objects.create(username="anna")
        jonas = User.objects.create(username="jonas")
        old = Message.objects.create(sender=anna, recipient=jonas, ciphertext="YQ==", iv="YQ==")
        recent = Message.objects.create(sender=anna, recipient=jonas, ciphertext="YQ==", iv="YQ==")
        Message.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=30))

        run("delete_old_messages")

        self.assertEqual(list(Message.objects.values_list("pk", flat=True)), [recent.pk])

    def test_consent_signing_key_prints_a_key_pair(self):
        output = StringIO()
        call_command("consent_signing_key", stdout=output)
        self.assertIn("PRIVATE KEY", output.getvalue())
        self.assertIn("PUBLIC KEY", output.getvalue())
