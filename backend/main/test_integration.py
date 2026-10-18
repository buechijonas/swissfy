import io
import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart
from django.utils import timezone

from posts.models import Post, Story, StoryLike, StoryView
from posts.tests import image_upload

User = get_user_model()
MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA)
class UserJourneyTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.anna = User.objects.create(username="anna")
        self.jonas = User.objects.create(username="jonas")
        self.mia = User.objects.create(username="mia")

    def as_user(self, user):
        self.client.force_login(user)

    def feed_ids(self):
        return [item["id"] for item in self.client.get("/api/posts/").json()["results"]]

    def notifications(self):
        return [
            item["message"] for item in self.client.get("/api/notifications/").json()["results"]
        ]

    def test_feed_follow_like_comment_repost(self):
        self.as_user(self.anna)
        post = self.client.post(
            "/api/posts/", {"text": "Hallo #zürich", "images": [image_upload()]}
        )
        self.assertEqual(post.status_code, 201)
        post_id = post.json()["id"]

        self.as_user(self.jonas)
        self.assertNotIn(post_id, self.feed_ids())
        self.client.post("/api/social/profiles/anna/follow/")
        self.assertIn(post_id, self.feed_ids())

        self.client.post(f"/api/posts/{post_id}/like/")
        self.client.post(f"/api/posts/{post_id}/comments/", {"text": "Schön!"})
        self.client.post(f"/api/posts/{post_id}/repost/")

        self.as_user(self.anna)
        self.assertEqual(
            self.notifications(),
            [
                "@jonas hat deinen Feed kommentiert: «Schön!»",
                "@jonas gefällt dein Feed.",
                "@jonas folgt dir jetzt.",
            ],
        )

        self.as_user(self.mia)
        self.client.post("/api/social/profiles/jonas/follow/")
        feed = self.client.get("/api/posts/").json()["results"]
        self.assertEqual([(item["id"], item["reposter"]) for item in feed], [(post_id, "jonas")])

        hashtag = self.client.get("/api/posts/hashtags/zürich/posts/").json()["results"]
        self.assertEqual([item["id"] for item in hashtag], [post_id])

    def test_private_profile_needs_an_accepted_follow_request(self):
        self.as_user(self.anna)
        self.client.patch(
            "/api/social/profiles/me/privacy/",
            {"profile_visibility": "followers"},
            content_type="application/json",
        )
        post_id = self.client.post("/api/posts/", {"text": "Privat"}).json()["id"]

        self.as_user(self.jonas)
        self.client.post("/api/social/profiles/anna/follow/")
        self.assertEqual(self.client.get(f"/api/posts/{post_id}/").status_code, 404)
        self.assertEqual(self.client.get("/api/social/profiles/anna/followers/").status_code, 403)

        self.as_user(self.anna)
        self.client.post("/api/social/profiles/me/follow-requests/jonas/")

        self.as_user(self.jonas)
        self.assertEqual(self.client.get(f"/api/posts/{post_id}/").status_code, 200)
        followers = self.client.get("/api/social/profiles/anna/followers/").json()["results"]
        self.assertEqual([user["username"] for user in followers], ["jonas"])

    def test_story_lifecycle_leaves_no_trace(self):
        self.as_user(self.anna)
        story_id = self.client.post(
            "/api/stories/", {"image": image_upload(), "text": "Heute"}
        ).json()["id"]

        self.as_user(self.jonas)
        post = Post.objects.create(author=self.anna, text="Hallo")
        author = self.client.get(f"/api/posts/{post.uuid}/").json()["author"]
        self.assertEqual((author["has_story"], author["story_seen"]), (True, False))
        self.client.post(f"/api/stories/{story_id}/view/")
        self.client.post(f"/api/stories/{story_id}/like/")
        author = self.client.get(f"/api/posts/{post.uuid}/").json()["author"]
        self.assertTrue(author["story_seen"])

        self.as_user(self.anna)
        story = self.client.get("/api/social/profiles/me/").json()["stories"][0]
        self.assertEqual((story["view_count"], story["like_count"]), ("1", "1"))
        viewers = self.client.get(f"/api/stories/{story_id}/viewers/").json()["results"]
        self.assertEqual([(user["username"], user["liked"]) for user in viewers], [("jonas", True)])

        Story.objects.update(created_at=timezone.now() - timedelta(hours=25))
        self.assertEqual(self.client.get("/api/social/profiles/me/").json()["stories"], [])
        call_command("delete_expired_stories", stdout=io.StringIO())
        self.assertFalse(Story.objects.exists())
        self.assertFalse(StoryView.objects.exists())
        self.assertFalse(StoryLike.objects.exists())

    def test_profile_pictures_follow_their_audience(self):
        self.as_user(self.anna)
        self.client.patch(
            "/api/social/profiles/me/pictures/",
            encode_multipart(
                BOUNDARY, {"public_picture": image_upload(), "private_picture": image_upload()}
            ),
            content_type=MULTIPART_CONTENT,
        )
        settings = self.client.get("/api/social/profiles/me/pictures/").json()
        self.assertIsNotNone(settings["public_picture"])
        self.assertIsNotNone(settings["private_picture"])
        self.assertNotEqual(settings["public_picture"], settings["private_picture"])

        self.as_user(self.jonas)
        picture = self.client.get("/api/social/profiles/anna/").json()["picture"]
        self.assertEqual(picture, settings["public_picture"])

        self.client.post("/api/social/profiles/anna/follow/")
        self.as_user(self.anna)
        self.client.post("/api/social/profiles/jonas/follow/")
        self.client.post("/api/social/profiles/jonas/friend-request/")
        self.as_user(self.jonas)
        self.client.post("/api/social/profiles/me/friend-requests/anna/")
        picture = self.client.get("/api/social/profiles/anna/").json()["picture"]
        self.assertEqual(picture, settings["private_picture"])
