import shutil
import tempfile
from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart

from accounts.models import UserProfile, get_or_create_profile
from chats.models import ChatRequest
from posts.models import ContactGroup
from posts.tests import image_upload

from .models import Follow, FollowRequest, FriendRequest, Friendship

User = get_user_model()
MEDIA = tempfile.mkdtemp()


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
        self.assertNotIn("count", data)
        self.assertEqual(len(data["results"]), 20)
        self.assertEqual(
            data["results"][0],
            {
                "username": "anna",
                "first_name": "",
                "last_name": "",
                "avatar": "",
                "picture": None,
                "role": None,
                "can_view": True,
            },
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

    def search(self, query):
        data = self.client.get("/api/social/profiles/", {"q": query}).json()
        return [user["username"] for user in data["results"]]

    def test_search(self):
        mia = User.objects.create(username="mia_s", first_name="Mia", last_name="Müller")
        User.objects.create(username="lukas", first_name="Lukas", last_name="Meier")
        self.assertEqual(self.search("mia"), ["mia_s"])
        self.assertEqual(self.search("müll"), ["mia_s"])
        self.assertEqual(self.search("  Mia   Müller "), ["mia_s"])
        self.assertEqual(self.search("m"), [])
        self.assertEqual(self.search("me"), ["lukas"])
        self.assertEqual(self.search("mi la"), [])
        self.assertEqual(self.search("mia mü"), ["mia_s"])
        self.assertEqual(self.search("xyz"), [])

        self.set_visibility(mia, profile_visibility="friends")
        self.assertEqual(self.search("müll"), [])
        self.assertEqual(self.search("mia müller"), ["mia_s"])
        self.assertEqual(self.search("Müller Mia"), ["mia_s"])
        self.assertEqual(self.search("mia_"), ["mia_s"])
        Friendship.objects.create(user=self.jonas, friend=mia)
        self.assertEqual(self.search("müll"), ["mia_s"])

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


class SearchOrderTests(TestCase):
    def test_staff_first_then_alphabetical(self):
        from accounts.roles import Role, set_role

        viewer = User.objects.create(username="viewer")
        names = {
            "zoe": Role.ADMIN,
            "bert": Role.MODERATOR,
            "carl": Role.SUPPORT,
            "anna": Role.VERIFIED,
            "aaron": Role.DEFAULT,
            "max": Role.MODERATOR,
        }
        for username, role in names.items():
            set_role(User.objects.create(username=username), role)
        for username, role in (("adam", Role.ADMIN), ("abby", Role.DEFAULT)):
            private = User.objects.create(username=username)
            set_role(private, role)
            UserProfile.objects.create(user=private, profile_visibility="friends")
        self.client.force_login(viewer)
        data = self.client.get("/api/social/profiles/").json()
        self.assertEqual(
            [user["username"] for user in data["results"]],
            ["zoe", "bert", "max", "carl", "anna", "aaron", "abby", "adam"],
        )


@override_settings(MEDIA_ROOT=MEDIA)
class PictureTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.jonas = User.objects.create(username="jonas")
        self.anna = User.objects.create(username="anna")
        self.client.force_login(self.jonas)

    def upload(self, **data):
        return self.client.patch(
            "/api/social/profiles/me/pictures/",
            encode_multipart(BOUNDARY, data),
            content_type=MULTIPART_CONTENT,
        )

    def picture_for(self, viewer):
        self.client.force_login(viewer)
        return self.client.get("/api/social/profiles/jonas/").json()["picture"]

    def test_without_upload_uses_govex_avatar(self):
        data = self.client.get("/api/social/profiles/me/").json()
        self.assertIsNone(data["picture"])

    def test_public_picture_is_square_and_visible_to_all(self):
        response = self.upload(public_picture=image_upload(2000, 1000))
        self.assertEqual(response.status_code, 200)
        url = response.json()["public_picture"]
        self.assertTrue(url.startswith("/api/social/profiles/jonas/pictures/public/?v="))

        self.assertEqual(self.picture_for(self.anna), url)
        image = self.client.get(url)
        self.assertEqual(image["Content-Type"], "image/webp")

    def test_private_picture_for_friends(self):
        self.upload(public_picture=image_upload(), private_picture=image_upload())
        settings = self.client.get("/api/social/profiles/me/pictures/").json()
        self.assertEqual(settings["private_picture_visibility"], "friends")

        self.assertEqual(self.picture_for(self.jonas), settings["private_picture"])
        self.assertEqual(self.picture_for(self.anna), settings["public_picture"])
        self.assertEqual(self.client.get(settings["private_picture"]).status_code, 404)

        Friendship.objects.create(user=self.anna, friend=self.jonas)
        self.assertEqual(self.picture_for(self.anna), settings["private_picture"])
        self.assertEqual(self.client.get(settings["private_picture"]).status_code, 200)

    def test_private_picture_for_followers(self):
        self.upload(private_picture=image_upload(), private_picture_visibility="followers")
        self.assertIsNone(self.picture_for(self.anna))
        Follow.objects.create(follower=self.anna, following=self.jonas)
        self.assertIsNotNone(self.picture_for(self.anna))

    def test_private_picture_for_groups(self):
        group = ContactGroup.objects.create(owner=self.jonas, name="Familie")
        response = self.upload(private_picture=image_upload(), private_picture_visibility="groups")
        self.assertEqual(response.status_code, 400)

        response = self.upload(
            private_picture=image_upload(),
            private_picture_visibility="groups",
            private_picture_groups=[group.pk],
        )
        self.assertEqual(response.json()["private_picture_groups"], [group.pk])
        self.assertIsNone(self.picture_for(self.anna))
        group.members.add(self.anna)
        self.assertIsNotNone(self.picture_for(self.anna))

    def test_foreign_groups_are_rejected(self):
        foreign = ContactGroup.objects.create(owner=self.anna, name="Fremd")
        response = self.upload(
            private_picture_visibility="groups", private_picture_groups=[foreign.pk]
        )
        self.assertEqual(response.status_code, 400)

    def test_remove_picture(self):
        self.upload(public_picture=image_upload())
        response = self.client.delete("/api/social/profiles/me/pictures/public/")
        self.assertIsNone(response.json()["public_picture"])
        self.assertIsNone(self.picture_for(self.anna))

    def test_invalid_upload(self):
        upload = SimpleUploadedFile("photo.jpg", b"no image", content_type="image/jpeg")
        self.assertEqual(self.upload(public_picture=upload).status_code, 400)

    def test_unknown_kind(self):
        self.assertEqual(
            self.client.get("/api/social/profiles/jonas/pictures/avatar/").status_code, 404
        )


class ConnectionListTests(TestCase):
    def setUp(self):
        self.jonas = User.objects.create(username="jonas")
        self.anna = User.objects.create(username="anna")
        self.eve = User.objects.create(username="eve")
        self.client.force_login(self.anna)

    def usernames(self, path, **params):
        response = self.client.get(f"/api/social/profiles/jonas/{path}/", params)
        self.assertEqual(response.status_code, 200)
        return [user["username"] for user in response.json()["results"]]

    def test_followers_following_and_friends(self):
        Follow.objects.create(follower=self.anna, following=self.jonas)
        Follow.objects.create(follower=self.eve, following=self.jonas)
        Follow.objects.create(follower=self.jonas, following=self.eve)
        Friendship.objects.create(user=self.jonas, friend=self.eve)

        self.assertEqual(self.usernames("followers"), ["anna", "eve"])
        self.assertEqual(self.usernames("following"), ["eve"])
        self.assertEqual(self.usernames("friends"), ["eve"])

    def test_search(self):
        Follow.objects.create(follower=self.anna, following=self.jonas)
        Follow.objects.create(follower=self.eve, following=self.jonas)
        self.assertEqual(self.usernames("followers", q="ev"), ["eve"])

    def test_private_profile(self):
        UserProfile.objects.create(user=self.jonas, profile_visibility="friends")
        response = self.client.get("/api/social/profiles/jonas/followers/")
        self.assertEqual(response.status_code, 403)

        Friendship.objects.create(user=self.anna, friend=self.jonas)
        self.assertEqual(self.usernames("friends"), [])

    def test_unknown_profile(self):
        response = self.client.get("/api/social/profiles/nobody/followers/")
        self.assertEqual(response.status_code, 404)
