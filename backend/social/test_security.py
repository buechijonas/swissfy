from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from accounts.models import UserProfile, get_or_create_profile
from moderation.models import Reason, Warning
from moderation.sanctions import suspend
from notifications.models import Notification

from .models import Follow, FollowRequest, FriendRequest, Friendship

User = get_user_model()


class PrivacyTests(TestCase):
    def setUp(self):
        self.anna = User.objects.create(username="anna", first_name="Anna", last_name="Geheim")
        self.eve = User.objects.create(username="eve")
        profile = get_or_create_profile(self.anna)
        profile.profile_visibility = UserProfile.Visibility.FRIENDS
        profile.birthdate = date(2000, 1, 31)
        profile.save()
        self.client.force_login(self.eve)

    def test_private_profile_hides_personal_data(self):
        data = self.client.get("/api/social/profiles/anna/").json()
        for field in ["first_name", "last_name", "role", "birthdate", "follower_count"]:
            self.assertNotIn(field, data)
        listed = self.client.get("/api/social/profiles/").json()["results"]
        anna = next(user for user in listed if user["username"] == "anna")
        self.assertNotIn("first_name", anna)

    def test_search_does_not_reveal_hidden_names(self):
        for query in ["Geheim", "geh", "Anna Geh", "nna Gehei"]:
            with self.subTest(query=query):
                results = self.client.get("/api/social/profiles/", {"q": query}).json()["results"]
                self.assertEqual(results, [])

    def test_birthdate_is_hidden_unless_shared(self):
        profile = get_or_create_profile(self.anna)
        profile.profile_visibility = UserProfile.Visibility.PUBLIC
        profile.save()
        self.assertNotIn("birthdate", self.client.get("/api/social/profiles/anna/").json())
        profile.show_birthdate = True
        profile.save()
        self.assertEqual(
            self.client.get("/api/social/profiles/anna/").json()["birthdate"], "2000-01-31"
        )

    def test_achievements_of_private_profiles_are_hidden(self):
        response = self.client.get("/api/social/profiles/anna/achievements/")
        self.assertEqual(response.status_code, 403)

    def test_privacy_endpoint_cannot_change_managed_fields(self):
        self.client.patch(
            "/api/social/profiles/me/privacy/",
            {
                "govex_sub": "stolen",
                "avatar": "owl",
                "birthdate": "1900-01-01",
                "chat_protection": "pin",
                "user": self.anna.pk,
            },
            content_type="application/json",
        )
        profile = get_or_create_profile(self.eve)
        self.assertIsNone(profile.govex_sub)
        self.assertEqual(profile.avatar, "")
        self.assertIsNone(profile.birthdate)
        self.assertEqual(profile.chat_protection, "standard")
        self.assertEqual(get_or_create_profile(self.anna).govex_sub, None)

    def test_privacy_values_must_be_known(self):
        response = self.client.patch(
            "/api/social/profiles/me/privacy/",
            {"profile_visibility": "everyone"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_suspended_users_are_hidden(self):
        warning = Warning.objects.create(user=self.anna, reason=Reason.INSULT)
        suspend(self.anna, warning, 0, timezone.now())
        self.assertEqual(self.client.get("/api/social/profiles/anna/").status_code, 404)
        usernames = [
            u["username"] for u in self.client.get("/api/social/profiles/").json()["results"]
        ]
        self.assertNotIn("anna", usernames)


class RelationTests(TestCase):
    def setUp(self):
        self.anna = User.objects.create(username="anna")
        self.jonas = User.objects.create(username="jonas")
        self.eve = User.objects.create(username="eve")
        profile = get_or_create_profile(self.anna)
        profile.profile_visibility = UserProfile.Visibility.FOLLOWERS
        profile.save()
        self.client.force_login(self.eve)

    def test_following_a_private_profile_only_creates_a_request(self):
        self.client.post("/api/social/profiles/anna/follow/")
        self.assertFalse(Follow.objects.filter(follower=self.eve, following=self.anna).exists())
        self.assertTrue(FollowRequest.objects.filter(follower=self.eve).exists())

    def test_cannot_accept_follow_requests_for_others(self):
        FollowRequest.objects.create(follower=self.jonas, following=self.anna)
        response = self.client.post("/api/social/profiles/me/follow-requests/jonas/")
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Follow.objects.filter(follower=self.jonas).exists())

    def test_cannot_accept_own_follow_request(self):
        self.client.post("/api/social/profiles/anna/follow/")
        response = self.client.post("/api/social/profiles/me/follow-requests/anna/")
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Follow.objects.filter(follower=self.eve).exists())

    def test_friendship_cannot_be_forced(self):
        response = self.client.post("/api/social/profiles/anna/friend-request/")
        self.assertEqual(response.status_code, 400)
        FriendRequest.objects.create(sender=self.jonas, receiver=self.anna)
        response = self.client.post("/api/social/profiles/me/friend-requests/jonas/")
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Friendship.objects.exists())

    def test_cannot_follow_self(self):
        self.assertEqual(self.client.post("/api/social/profiles/eve/follow/").status_code, 400)


class NotificationTests(TestCase):
    def test_notifications_are_private(self):
        anna = User.objects.create(username="anna")
        eve = User.objects.create(username="eve")
        Notification.objects.create(recipient=anna, kind=Notification.Kind.FOLLOW, actor=eve)
        self.client.force_login(eve)
        self.assertEqual(self.client.get("/api/notifications/").json()["results"], [])
        self.assertEqual(self.client.get("/api/notifications/unread/").json()["count"], 0)
        self.client.post("/api/notifications/read/")
        self.assertIsNone(Notification.objects.get().read_at)
