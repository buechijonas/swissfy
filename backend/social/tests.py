import shutil
import tempfile
from datetime import date
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart

from accounts.models import UserProfile, get_or_create_profile
from chats.models import ChatRequest
from posts.models import ContactGroup, Post
from posts.tests import image_upload

from . import library
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


class ProfileMediaTests(TestCase):
    def setUp(self):
        self.jonas = User.objects.create(username="jonas")
        self.anna = User.objects.create(username="anna")
        self.client.force_login(self.anna)

    def media(self):
        return self.client.get("/api/social/profiles/jonas/").json()["media"]

    def test_media_flags(self):
        self.assertEqual(self.media(), {"pictures": False, "reels": False})
        Post.objects.create(author=self.jonas, text="Text")
        Post.objects.create(author=self.jonas, video="v.mp4", video_status="processing")
        self.assertEqual(self.media(), {"pictures": False, "reels": False})

        Post.objects.create(author=self.jonas, video="v.mp4", video_status="ready")
        self.assertEqual(self.media(), {"pictures": False, "reels": True})
        Post.objects.create(author=self.jonas, thumbnail="t.webp")
        self.assertEqual(self.media(), {"pictures": True, "reels": True})

    def test_media_respects_visibility(self):
        Post.objects.create(author=self.jonas, thumbnail="t.webp", visibility="friends")
        self.assertEqual(self.media(), {"pictures": False, "reels": False})


def movie(id):
    return {"id": id, "title": f"Film {id}", "year": "2001", "cover": f"imdb/{id}"}


def suggestion(id, qid, image="MV5Bposter@"):
    return {
        "id": id,
        "qid": qid,
        "l": f"Titel {id}",
        "y": 2017,
        "i": {"imageUrl": f"https://m.media-amazon.com/images/M/{image}._V1_.jpg"},
    }


class AboutTests(TestCase):
    URL = "/api/social/profiles/me/about/"

    def setUp(self):
        self.jonas = User.objects.create(username="jonas")
        self.anna = User.objects.create(username="anna")
        self.client.force_login(self.jonas)

    def patch(self, data):
        return self.client.patch(self.URL, data, content_type="application/json")

    def test_saves_biography_and_favorites(self):
        with mock.patch("social.library.details", side_effect=lambda kind, id: movie(id)):
            response = self.patch({"biography": "Hallo", "favorite_movies": ["tt1", "tt2", "tt2"]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["biography"], "Hallo")
        self.assertEqual(
            response.json()["favorite_movies"],
            [
                {
                    "id": "tt1",
                    "title": "Film tt1",
                    "year": "2001",
                    "cover": "/api/social/covers/imdb/tt1",
                },
                {
                    "id": "tt2",
                    "title": "Film tt2",
                    "year": "2001",
                    "cover": "/api/social/covers/imdb/tt2",
                },
            ],
        )
        self.assertEqual(
            get_or_create_profile(self.jonas).favorite_movies, [movie("tt1"), movie("tt2")]
        )

        with mock.patch("social.library.details") as details:
            self.patch({"favorite_movies": ["tt2"]})
        details.assert_not_called()
        self.assertEqual(get_or_create_profile(self.jonas).favorite_movies, [movie("tt2")])

    def test_limits_favorites(self):
        response = self.patch({"favorite_games": ["tt1", "tt2", "tt3", "tt4"]})
        self.assertEqual(response.status_code, 400)

    def test_rejects_unknown_or_wrong_kind(self):
        with mock.patch(
            "social.library.imdb_suggestions", return_value=[suggestion("tt1", "movie")]
        ):
            self.assertEqual(self.patch({"favorite_games": ["tt1"]}).status_code, 400)
            self.assertEqual(self.patch({"favorite_movies": ["../x"]}).status_code, 400)
            self.assertEqual(self.patch({"favorite_movies": ["tt1"]}).status_code, 200)

    def test_library_unavailable(self):
        with mock.patch(
            "social.library.requests.get", side_effect=library.requests.ConnectionError
        ):
            response = self.patch({"favorite_series": ["tt1"]})
        self.assertEqual(response.status_code, 503)

    def test_profile_shows_about_only_when_visible(self):
        UserProfile.objects.create(user=self.anna, biography="Hi", favorite_games=[movie("tt5")])
        data = self.client.get("/api/social/profiles/anna/").json()
        self.assertEqual(data["biography"], "Hi")
        self.assertEqual(data["favorite_games"][0]["cover"], "/api/social/covers/imdb/tt5")

        UserProfile.objects.filter(user=self.anna).update(profile_visibility="friends")
        data = self.client.get("/api/social/profiles/anna/").json()
        self.assertNotIn("biography", data)
        self.assertNotIn("favorite_games", data)

    def test_search_filters_by_kind(self):
        results = [
            suggestion("tt7", "tvSeries"),
            suggestion("tt8", "movie"),
            {"id": "nm1", "l": "Person"},
            suggestion("tt9", "tvMiniSeries", image="evil/../x"),
        ]
        response = mock.Mock(json=lambda: {"d": results})
        with mock.patch("social.library.requests.get", return_value=response) as get:
            data = self.client.get("/api/social/library/series/?q=Dark Matter").json()
        self.assertEqual(
            get.call_args.args[0], "https://v3.sg.media-imdb.com/suggestion/x/dark%20matter.json"
        )
        self.assertEqual(
            data["results"],
            [
                {
                    "id": "tt7",
                    "title": "Titel tt7",
                    "year": "2017",
                    "cover": "/api/social/covers/imdb/MV5Bposter@",
                },
                {"id": "tt9", "title": "Titel tt9", "year": "2017", "cover": None},
            ],
        )
        self.assertEqual(self.client.get("/api/social/library/books/?q=x").status_code, 404)

    def test_game_search_and_details_from_steam(self):
        search = mock.Mock(json=lambda: {"items": [{"id": 620, "name": "Portal 2"}]})
        with mock.patch("social.library.requests.get", return_value=search) as get:
            data = self.client.get("/api/social/library/games/?q=portal").json()
        self.assertEqual(get.call_args.kwargs["params"]["term"], "portal")
        self.assertEqual(
            data["results"],
            [
                {
                    "id": "620",
                    "title": "Portal 2",
                    "year": "",
                    "cover": "/api/social/covers/steam/620",
                }
            ],
        )

        app = {"success": True, "data": {"type": "game", "name": "Portal 2"}}
        app["data"]["release_date"] = {"date": "18. Apr. 2011"}
        with mock.patch("social.library.fetch", return_value={"620": app}):
            self.assertEqual(self.patch({"favorite_games": ["620"]}).status_code, 200)
        self.assertEqual(
            get_or_create_profile(self.jonas).favorite_games,
            [{"id": "620", "title": "Portal 2", "year": "2011", "cover": "steam/620"}],
        )

        app["data"]["type"] = "dlc"
        with mock.patch("social.library.fetch", return_value={"621": app}):
            self.assertEqual(self.patch({"favorite_games": ["621"]}).status_code, 400)

    def test_cover_only_from_known_sources(self):
        for path in ["imdb/../x", "evil/x", "imdb/a.jpg", "imdb/a/b", "steam/abc", "steam/1/x"]:
            with self.subTest(path=path):
                self.assertEqual(library.cover_urls(path), [])
                self.assertEqual(self.client.get(f"/api/social/covers/{path}").status_code, 404)

    def test_steam_cover_falls_back_to_header(self):
        missing = mock.Mock(raise_for_status=mock.Mock(side_effect=library.requests.HTTPError))
        found = mock.Mock(content=b"img", headers={"Content-Type": "image/jpeg"})
        with mock.patch("social.library.requests.get", side_effect=[missing, found]) as get:
            served = self.client.get("/api/social/covers/steam/620")
        self.assertTrue(get.call_args.args[0].endswith("/apps/620/header.jpg"))
        self.assertEqual(served.content, b"img")

    def test_cover_proxy(self):
        response = mock.Mock(content=b"img", headers={"Content-Type": "image/jpeg"})
        with mock.patch("social.library.requests.get", return_value=response) as get:
            served = self.client.get("/api/social/covers/imdb/MV5Bposter@")
        get.assert_called_once_with(
            "https://m.media-amazon.com/images/M/MV5Bposter@._V1_UX342_.jpg", timeout=10
        )
        self.assertEqual((served.status_code, served.content), (200, b"img"))
