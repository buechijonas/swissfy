from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import UserProfile, get_or_create_profile

from .models import Follow, FriendRequest, Friendship

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
            (data["follower_count"], data["following_count"], data["friend_count"]), (1, 0, 1)
        )

    def test_profile_list_excludes_self_and_pages(self):
        User.objects.bulk_create(User(username=f"user{i:02}") for i in range(25))
        data = self.client.get("/api/social/profiles/").json()
        self.assertEqual(data["count"], 26)
        self.assertEqual(len(data["results"]), 20)
        self.assertEqual(
            data["results"][0], {"username": "anna", "first_name": "", "last_name": "", "avatar": ""}
        )
        self.assertNotIn("jonas", [u["username"] for u in data["results"]])

        data = self.client.get(data["next"]).json()
        self.assertEqual(len(data["results"]), 6)
        self.assertIsNone(data["next"])

    def set_visibility(self, user, **fields):
        UserProfile.objects.filter(pk=get_or_create_profile(user).pk).update(**fields)

    def test_privacy_settings(self):
        data = self.client.get("/api/social/profiles/me/privacy/").json()
        self.assertEqual(data, {"profile_visibility": "public"})

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

    def test_profile_for_followers(self):
        self.anna.first_name = "Anna"
        self.anna.save()
        self.set_visibility(self.anna, profile_visibility="followers")

        data = self.client.get("/api/social/profiles/anna/").json()
        self.assertFalse(data["can_view"])
        self.assertIsNone(data["follower_count"])
        self.assertEqual(data["first_name"], "")

        self.follow(self.jonas, self.anna)
        data = self.client.get("/api/social/profiles/anna/").json()
        self.assertTrue(data["can_view"])
        self.assertEqual(data["follower_count"], 1)
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
        self.assertEqual(data["results"][0]["first_name"], "")

        self.follow(self.jonas, self.anna)
        data = self.client.get("/api/social/profiles/").json()
        self.assertEqual(data["results"][0]["first_name"], "Anna")

    def test_unknown_profile(self):
        self.assertEqual(self.client.get("/api/social/profiles/nobody/").status_code, 404)

    def test_follow_and_unfollow(self):
        data = self.client.post("/api/social/profiles/anna/follow/").json()
        self.assertTrue(data["is_following"])
        self.assertEqual(data["follower_count"], 1)

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
