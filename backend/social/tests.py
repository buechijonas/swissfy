from django.contrib.auth import get_user_model
from django.test import TestCase

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
