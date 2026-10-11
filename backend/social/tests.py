from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import UserProfile, get_or_create_profile
from chats.models import ChatRequest

from .models import Follow, FollowRequest, FriendRequest, Friendship

User = get_user_model()


class ProfileTests(TestCase):
    def setUp(self):
        self.jonas = User.objects.create(username="jonas", first_name="Jonas")
        self.anna = User.objects.create(username="anna")
        self.client.force_login(self.jonas)

    def follow(self, follower, following):
        Follow.objects.create(follower=follower, following=following)

    def test_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.get("/api/social/profiles/me/").status_code, 403)

    def test_own_profile_counts(self):
        self.follow(self.anna, self.jonas)
        Friendship.objects.create(user=self.jonas, friend=self.anna)
        data = self.client.get("/api/social/profiles/me/").json()
        self.assertEqual(data["username"], "jonas")
        self.assertEqual(data["first_name"], "Jonas")
        self.assertTrue(data["is_self"])
        self.assertEqual(
            (data["follower_count"], data["following_count"], data["friend_count"]), ("1", "0", "1")
        )

    def test_profile_list_excludes_self_and_pages(self):
        User.objects.bulk_create(User(username=f"user{i:02}") for i in range(25))
        data = self.client.get("/api/social/profiles/").json()
        self.assertEqual(data["count"], 26)
        self.assertEqual(len(data["results"]), 20)
        self.assertEqual(
            data["results"][0],
            {"username": "anna", "first_name": "", "last_name": "", "avatar": "", "can_view": True},
        )
        self.assertNotIn("jonas", [u["username"] for u in data["results"]])

        data = self.client.get(data["next"]).json()
        self.assertEqual(len(data["results"]), 6)
        self.assertIsNone(data["next"])

    def set_visibility(self, user, **fields):
        UserProfile.objects.filter(pk=get_or_create_profile(user).pk).update(**fields)

    def test_privacy_settings(self):
        data = self.client.get("/api/social/profiles/me/privacy/").json()
        self.assertEqual(
            data,
            {
                "profile_visibility": "public",
                "read_receipts": True,
                "chat_requests": True,
                "show_birthdate": False,
            },
        )

        response = self.client.patch(
            "/api/social/profiles/me/privacy/",
            {"profile_visibility": "friends"},
            content_type="application/json",
        )
        self.assertEqual(response.json()["profile_visibility"], "friends")
        self.assertEqual(get_or_create_profile(self.jonas).profile_visibility, "friends")

        response = self.client.patch(
            "/api/social/profiles/me/privacy/",
            {"profile_visibility": "everyone"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_birthdate_only_when_shown(self):
        profile = get_or_create_profile(self.anna)
        profile.birthdate = date(2000, 1, 31)
        profile.save()
        self.assertNotIn("birthdate", self.client.get("/api/social/profiles/anna/").json())
        self.client.force_login(self.anna)
        self.assertEqual(
            self.client.get("/api/social/profiles/me/").json()["birthdate"], "2000-01-31"
        )
        self.client.force_login(self.jonas)

        self.set_visibility(self.anna, show_birthdate=True)
        data = self.client.get("/api/social/profiles/anna/").json()
        self.assertEqual(data["birthdate"], "2000-01-31")

        self.set_visibility(self.anna, profile_visibility="friends")
        self.assertNotIn("birthdate", self.client.get("/api/social/profiles/anna/").json())

    def test_profile_for_followers(self):
        self.anna.first_name = "Anna"
        self.anna.save()
        self.set_visibility(self.anna, profile_visibility="followers")

        data = self.client.get("/api/social/profiles/anna/").json()
        self.assertFalse(data["can_view"])
        for field in ["first_name", "last_name", "follower_count"]:
            self.assertNotIn(field, data)

        self.follow(self.jonas, self.anna)
        data = self.client.get("/api/social/profiles/anna/").json()
        self.assertTrue(data["can_view"])
        self.assertEqual(data["follower_count"], "1")
        self.assertEqual(data["first_name"], "Anna")

    def test_profile_for_friends(self):
        self.set_visibility(self.anna, profile_visibility="friends")
        self.follow(self.jonas, self.anna)
        self.assertFalse(self.client.get("/api/social/profiles/anna/").json()["can_view"])

        Friendship.objects.create(user=self.jonas, friend=self.anna)
        self.assertTrue(self.client.get("/api/social/profiles/anna/").json()["can_view"])

    def test_own_profile_ignores_visibility(self):
        self.set_visibility(self.jonas, profile_visibility="friends")
        data = self.client.get("/api/social/profiles/me/").json()
        self.assertTrue(data["can_view"])
        self.assertEqual(data["first_name"], "Jonas")

    def test_profile_list_hides_name(self):
        self.anna.first_name = "Anna"
        self.anna.save()
        self.set_visibility(self.anna, profile_visibility="followers")
        data = self.client.get("/api/social/profiles/").json()
        self.assertNotIn("first_name", data["results"][0])
        self.assertFalse(data["results"][0]["can_view"])

        self.follow(self.jonas, self.anna)
        data = self.client.get("/api/social/profiles/").json()
        self.assertEqual(data["results"][0]["first_name"], "Anna")

    def test_unknown_profile(self):
        self.assertEqual(self.client.get("/api/social/profiles/nobody/").status_code, 404)

    def test_follow_and_unfollow(self):
        data = self.client.post("/api/social/profiles/anna/follow/").json()
        self.assertTrue(data["is_following"])
        self.assertEqual(data["follower_count"], "1")

        data = self.client.delete("/api/social/profiles/anna/follow/").json()
        self.assertFalse(data["is_following"])
        self.assertFalse(Follow.objects.exists())

    def test_cannot_follow_self(self):
        response = self.client.post("/api/social/profiles/jonas/follow/")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Follow.objects.exists())

    def test_friend_request_needs_mutual_follow(self):
        self.follow(self.jonas, self.anna)
        response = self.client.post("/api/social/profiles/anna/friend-request/")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(FriendRequest.objects.exists())

    def test_friend_request_with_mutual_follow(self):
        self.follow(self.jonas, self.anna)
        self.follow(self.anna, self.jonas)
        data = self.client.post("/api/social/profiles/anna/friend-request/").json()
        self.assertTrue(data["friend_request_sent"])
        self.assertTrue(
            FriendRequest.objects.filter(sender=self.jonas, receiver=self.anna).exists()
        )

    def test_no_friend_request_to_friends(self):
        self.follow(self.jonas, self.anna)
        self.follow(self.anna, self.jonas)
        Friendship.objects.create(user=self.jonas, friend=self.anna)
        response = self.client.post("/api/social/profiles/anna/friend-request/")
        self.assertEqual(response.status_code, 400)


class FollowRequestTests(TestCase):
    def setUp(self):
        self.jonas = User.objects.create(username="jonas")
        self.anna = User.objects.create(username="anna", first_name="Anna")
        profile = get_or_create_profile(self.anna)
        profile.profile_visibility = "followers"
        profile.save()
        self.client.force_login(self.jonas)

    def test_follow_private_profile_sends_request(self):
        data = self.client.post("/api/social/profiles/anna/follow/").json()
        self.assertTrue(data["requires_follow_request"])
        self.assertTrue(data["follow_requested"])
        self.assertFalse(data["is_following"])
        self.assertFalse(data["can_view"])
        self.assertFalse(Follow.objects.exists())

    def test_cancel_request(self):
        self.client.post("/api/social/profiles/anna/follow/")
        data = self.client.delete("/api/social/profiles/anna/follow/").json()
        self.assertFalse(data["follow_requested"])
        self.assertFalse(FollowRequest.objects.exists())

    def test_accept_request(self):
        self.client.post("/api/social/profiles/anna/follow/")
        self.client.force_login(self.anna)
        data = self.client.get("/api/social/profiles/me/follow-requests/").json()
        self.assertEqual([user["username"] for user in data], ["jonas"])

        response = self.client.post("/api/social/profiles/me/follow-requests/jonas/")
        self.assertEqual(response.status_code, 204)
        self.assertTrue(Follow.objects.filter(follower=self.jonas, following=self.anna).exists())
        self.assertFalse(FollowRequest.objects.exists())

        self.client.force_login(self.jonas)
        data = self.client.get("/api/social/profiles/anna/").json()
        self.assertTrue(data["can_view"])
        self.assertEqual(data["first_name"], "Anna")

    def test_decline_request(self):
        self.client.post("/api/social/profiles/anna/follow/")
        self.client.force_login(self.anna)
        response = self.client.delete("/api/social/profiles/me/follow-requests/jonas/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(FollowRequest.objects.exists())
        self.assertFalse(Follow.objects.exists())

    def test_cannot_accept_foreign_request(self):
        eve = User.objects.create(username="eve")
        FollowRequest.objects.create(follower=eve, following=self.anna)
        response = self.client.post("/api/social/profiles/me/follow-requests/eve/")
        self.assertEqual(response.status_code, 404)

    def test_friends_only_profile_also_needs_request(self):
        profile = get_or_create_profile(self.anna)
        profile.profile_visibility = "friends"
        profile.save()
        self.client.post("/api/social/profiles/anna/follow/")
        self.assertTrue(FollowRequest.objects.exists())

    def test_going_public_accepts_requests(self):
        self.client.post("/api/social/profiles/anna/follow/")
        self.client.force_login(self.anna)
        self.client.patch(
            "/api/social/profiles/me/privacy/",
            {"profile_visibility": "public"},
            content_type="application/json",
        )
        self.assertTrue(Follow.objects.filter(follower=self.jonas, following=self.anna).exists())
        self.assertFalse(FollowRequest.objects.exists())


class CanChatTests(TestCase):
    def setUp(self):
        self.jonas = User.objects.create(username="jonas")
        self.anna = User.objects.create(username="anna")
        self.client.force_login(self.jonas)

    def can_chat(self):
        return self.client.get("/api/social/profiles/anna/").json()["can_chat"]

    def test_can_chat(self):
        self.assertTrue(self.can_chat())
        self.assertFalse(self.client.get("/api/social/profiles/me/").json()["can_chat"])

    def test_requests_disabled(self):
        profile = get_or_create_profile(self.anna)
        profile.chat_requests = False
        profile.save()
        self.assertFalse(self.can_chat())

        ChatRequest.objects.create(sender=self.jonas, recipient=self.anna, status="accepted")
        self.assertTrue(self.can_chat())
