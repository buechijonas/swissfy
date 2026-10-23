from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from accounts.models import UserProfile, get_or_create_profile
from accounts.roles import Role, set_role
from moderation.models import Report, Warning
from posts.models import Post
from social.models import Follow, FriendRequest, Friendship

from .models import Notification

User = get_user_model()


class NotificationTests(TestCase):
    def setUp(self):
        self.anna = User.objects.create(username="anna")
        self.jonas = User.objects.create(username="jonas")
        self.post = Post.objects.create(author=self.anna, text="Hallo")

    def inbox(self, user=None):
        self.client.force_login(user or self.anna)
        return self.client.get("/api/notifications/").json()["results"]

    def unread(self):
        return self.client.get("/api/notifications/unread/").json()["count"]

    def test_comment_like_and_follow(self):
        self.client.force_login(self.jonas)
        self.client.post(f"/api/posts/{self.post.uuid}/comments/", {"text": "Schön!"})
        self.client.post(f"/api/posts/{self.post.uuid}/like/")
        self.client.post("/api/social/profiles/anna/follow/")

        items = self.inbox()
        self.assertEqual(
            [item["message"] for item in items],
            [
                "@jonas folgt dir jetzt.",
                "@jonas gefällt dein Feed.",
                "@jonas hat deinen Feed kommentiert: «Schön!»",
            ],
        )
        self.assertEqual(self.unread(), 3)
        self.client.post("/api/notifications/read/")
        self.assertEqual(self.unread(), 0)

        self.client.force_login(self.jonas)
        self.client.delete(f"/api/posts/{self.post.uuid}/like/")
        self.assertEqual(len(self.inbox()), 2)

    def test_own_actions_do_not_notify(self):
        self.client.force_login(self.anna)
        self.client.post(f"/api/posts/{self.post.uuid}/like/")
        self.assertEqual(self.inbox(), [])

    def test_friend_request_can_be_answered(self):
        Follow.objects.create(follower=self.anna, following=self.jonas)
        Follow.objects.create(follower=self.jonas, following=self.anna)
        self.client.force_login(self.jonas)
        self.client.post("/api/social/profiles/anna/friend-request/")

        self.assertEqual(self.inbox()[0]["request"], "pending")
        self.client.post("/api/social/profiles/me/friend-requests/jonas/")
        self.assertTrue(Friendship.objects.filter(user=self.anna, friend=self.jonas).exists())
        self.assertFalse(FriendRequest.objects.exists())
        self.assertEqual(self.inbox()[0]["request"], "accepted")

    def test_warning_and_suspension_hide_moderator(self):
        mod = User.objects.create(username="mod")
        set_role(mod, Role.MODERATOR)
        for number in range(3):
            post = Post.objects.create(author=self.anna, text=str(number))
            Report.objects.create(reporter=self.jonas, post=post)
            self.client.force_login(mod)
            self.client.post(f"/api/moderation/posts/{post.uuid}/warnings/", {"reason": "spam"})

        items = self.inbox()
        self.assertEqual(items[0]["message"].split(",")[0], "Dein Konto wurde für 3 Tage gesperrt")
        self.assertEqual(items[1]["message"], "Du wurdest verwarnt: Spam.")
        self.assertTrue(all(item["actor"] is None for item in items))

    def test_expired_warning_notifies_once(self):
        warning = Warning.objects.create(user=self.anna, reason="spam")
        Warning.objects.filter(pk=warning.pk).update(created_at=timezone.now() - timedelta(days=91))
        self.client.force_login(self.anna)
        self.assertEqual(self.unread(), 1)
        self.inbox()
        self.assertEqual(
            Notification.objects.filter(kind=Notification.Kind.WARNING_EXPIRED).count(), 1
        )
        self.assertIn("ist verjährt", self.inbox()[0]["message"])

    def test_old_friend_request_keeps_its_decision(self):
        Follow.objects.create(follower=self.anna, following=self.jonas)
        Follow.objects.create(follower=self.jonas, following=self.anna)
        self.client.force_login(self.jonas)
        self.client.post("/api/social/profiles/anna/friend-request/")
        self.client.force_login(self.anna)
        self.client.delete("/api/social/profiles/me/friend-requests/jonas/")
        self.client.force_login(self.jonas)
        self.client.post("/api/social/profiles/anna/friend-request/")

        states = [item["request"] for item in self.inbox()]
        self.assertEqual(states, ["pending", "declined"])

    def make_private(self):
        profile = get_or_create_profile(self.anna)
        profile.profile_visibility = UserProfile.Visibility.FRIENDS
        profile.save()

    def test_follow_request_can_be_answered(self):
        self.make_private()
        self.client.force_login(self.jonas)
        self.client.post("/api/social/profiles/anna/follow/")

        item = self.inbox()[0]
        self.assertEqual(item["message"], "@jonas möchte dir folgen.")
        self.assertEqual(item["request"], "pending")
        self.client.post("/api/social/profiles/me/follow-requests/jonas/")
        self.assertTrue(Follow.objects.filter(follower=self.jonas, following=self.anna).exists())
        self.assertEqual(self.inbox()[0]["request"], "accepted")

    def test_withdrawn_follow_request_removes_notification(self):
        self.make_private()
        self.client.force_login(self.jonas)
        self.client.post("/api/social/profiles/anna/follow/")
        self.client.delete("/api/social/profiles/anna/follow/")
        self.assertEqual(self.inbox(), [])

    def test_going_public_accepts_follow_requests(self):
        self.make_private()
        self.client.force_login(self.jonas)
        self.client.post("/api/social/profiles/anna/follow/")
        self.client.force_login(self.anna)
        self.client.patch(
            "/api/social/profiles/me/privacy/",
            {"profile_visibility": "public"},
            content_type="application/json",
        )
        self.assertEqual(self.inbox()[0]["request"], "accepted")
