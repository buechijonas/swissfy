import io
import shutil
import subprocess
import tempfile
from datetime import timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image

from accounts.models import get_or_create_profile
from accounts.roles import Role, set_role
from social.models import Follow, Friendship

from .models import (
    Album,
    Comment,
    ContactGroup,
    Post,
    PostCreation,
    Repost,
    SavedFolder,
    Story,
    StoryLike,
    StoryView,
)

User = get_user_model()
MEDIA = tempfile.mkdtemp()


def image_upload(width=2000, height=1000, exif=True):
    image = Image.new("RGB", (width, height), "red")
    data = io.BytesIO()
    metadata = Image.Exif()
    if exif:
        metadata[0x010E] = "secret"
    image.save(data, format="JPEG", exif=metadata)
    return SimpleUploadedFile("photo.jpg", data.getvalue(), content_type="image/jpeg")


@override_settings(MEDIA_ROOT=MEDIA)
class PostTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.jonas = User.objects.create(username="jonas")
        self.anna = User.objects.create(username="anna")
        self.eve = User.objects.create(username="eve")
        self.client.force_login(self.anna)

    def post(self, **data):
        return self.client.post("/api/posts/", {"text": "Hallo", **data})

    def as_user(self, user):
        self.client.force_login(user)

    def visible_ids(self, username="anna"):
        data = self.client.get(f"/api/posts/users/{username}/").json()
        return [post["id"] for post in data["results"]]

    def befriend(self, user, other):
        Friendship.objects.create(user=user, friend=other)
        Friendship.objects.create(user=other, friend=user)

    def test_create_text_post(self):
        response = self.post()
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual((data["text"], data["images"], data["is_own"]), ("Hallo", [], True))
        self.assertEqual(data["author"]["username"], "anna")

    def test_empty_post_is_rejected(self):
        self.assertEqual(self.post(text=" ").status_code, 400)
        self.assertEqual(self.post(text="x" * 501).status_code, 400)

    def image_size(self, url):
        response = self.client.get(url)
        with Image.open(io.BytesIO(b"".join(response.streaming_content))) as image:
            return image.size

    def test_image_is_compressed_and_stripped(self):
        data = self.post(images=[image_upload()]).json()
        self.assertEqual((data["aspect_ratio"], data["list_aspect_ratio"]), (2, 2))

        response = self.client.get(data["images"][0])
        self.assertEqual(response["Content-Type"], "image/webp")
        self.assertIn("private", response["Cache-Control"])
        with Image.open(io.BytesIO(b"".join(response.streaming_content))) as image:
            self.assertEqual(image.format, "WEBP")
            self.assertFalse(image.getexif())

        self.assertEqual(self.image_size(data["thumbnail"]), (400, 400))

    def test_images_are_cropped_to_first_ratio(self):
        square, landscape = image_upload(1000, 1000), image_upload(2000, 1000)
        data = self.post(images=[square, landscape]).json()
        self.assertEqual([self.image_size(url) for url in data["images"]], [(1000, 1000)] * 2)

        square, landscape = image_upload(1000, 1000), image_upload(2000, 1000)
        data = self.post(images=[landscape, square]).json()
        self.assertEqual([self.image_size(url) for url in data["images"]], [(1280, 640)] * 2)

    def test_invalid_image_is_rejected(self):
        upload = SimpleUploadedFile("x.jpg", b"no image", content_type="image/jpeg")
        self.assertEqual(self.post(images=[image_upload(), upload]).status_code, 400)
        uploads = [image_upload(10, 10) for _ in range(11)]
        self.assertEqual(self.post(images=uploads).status_code, 400)
        self.assertFalse(Post.objects.exists())

    def remaining(self):
        return self.client.get("/api/posts/quota/").json()["remaining"]

    def test_posts_per_day_are_limited(self):
        old = self.post().json()["id"]
        PostCreation.objects.update(created_at=timezone.now() - timedelta(days=2))
        for _ in range(9):
            self.post()
        self.assertEqual(self.remaining(), 1)

        last = self.post().json()["id"]
        self.assertEqual(self.post().status_code, 429)
        self.client.delete(f"/api/posts/{last}/")
        self.client.delete(f"/api/posts/{old}/")
        self.assertEqual(self.remaining(), 0)
        self.assertEqual(self.post().status_code, 429)
        self.assertEqual(PostCreation.objects.count(), 10)

    def test_audiences(self):
        group = ContactGroup.objects.create(owner=self.anna, name="Familie")
        group.members.add(self.eve)
        ids = {
            visibility: self.post(visibility=visibility).json()["id"]
            for visibility in ("public", "followers", "friends")
        }
        ids["groups"] = self.post(visibility="groups", groups=[group.pk]).json()["id"]

        self.as_user(self.jonas)
        self.assertEqual(self.visible_ids(), [ids["public"]])
        Follow.objects.create(follower=self.jonas, following=self.anna)
        self.assertEqual(self.visible_ids(), [ids["followers"], ids["public"]])
        self.befriend(self.jonas, self.anna)
        self.assertEqual(self.visible_ids(), [ids["friends"], ids["followers"], ids["public"]])

        self.as_user(self.eve)
        self.assertEqual(self.visible_ids(), [ids["groups"], ids["public"]])
        self.assertEqual(self.client.get(f"/api/posts/{ids['friends']}/").status_code, 404)

    def test_private_profile_hides_public_posts(self):
        post = self.post().json()["id"]
        profile = get_or_create_profile(self.anna)
        profile.profile_visibility = "friends"
        profile.save()

        self.as_user(self.jonas)
        self.assertEqual(self.visible_ids(), [])
        self.assertEqual(self.client.get(f"/api/posts/{post}/images/0/").status_code, 404)

    def test_groups_post_needs_own_group(self):
        self.assertEqual(self.post(visibility="groups").status_code, 400)
        foreign = ContactGroup.objects.create(owner=self.jonas, name="Fremd")
        self.assertEqual(self.post(visibility="groups", groups=[foreign.pk]).status_code, 400)

    def test_author_changes_visibility(self):
        post = self.post().json()["id"]
        group = ContactGroup.objects.create(owner=self.anna, name="Familie")
        group.members.add(self.jonas)

        self.as_user(self.jonas)
        response = self.client.patch(
            f"/api/posts/{post}/", {"visibility": "friends"}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)

        self.as_user(self.anna)
        response = self.client.patch(
            f"/api/posts/{post}/",
            {"visibility": "groups", "groups": [group.pk]},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            (response.json()["visibility"], response.json()["groups"]), ("groups", [group.pk])
        )
        self.as_user(self.eve)
        self.assertEqual(self.visible_ids(), [])

        self.as_user(self.anna)
        response = self.client.patch(
            f"/api/posts/{post}/", {"visibility": "public"}, content_type="application/json"
        )
        self.assertEqual(response.json()["groups"], [])
        self.as_user(self.eve)
        self.assertEqual(self.visible_ids(), [post])

    def test_visibility_change_needs_own_group(self):
        post = self.post().json()["id"]
        foreign = ContactGroup.objects.create(owner=self.jonas, name="Fremd")
        for data in (
            {"visibility": "groups"},
            {"visibility": "groups", "groups": [foreign.pk]},
            {},
        ):
            response = self.client.patch(
                f"/api/posts/{post}/", data, content_type="application/json"
            )
            self.assertEqual(response.status_code, 400)

    def test_feed_orders_by_day_with_friends_first(self):
        Follow.objects.create(follower=self.jonas, following=self.anna)
        Follow.objects.create(follower=self.jonas, following=self.eve)
        self.befriend(self.jonas, self.eve)
        yesterday = Post.objects.create(author=self.eve, text="gestern")
        Post.objects.filter(pk=yesterday.pk).update(created_at=timezone.now() - timedelta(days=1))
        friend = Post.objects.create(author=self.eve, text="Freundin")
        follow = Post.objects.create(author=self.anna, text="Folge")
        own = Post.objects.create(author=self.jonas, text="eigener")
        Post.objects.create(author=User.objects.create(username="mia"), text="fremd")

        self.as_user(self.jonas)
        data = self.client.get("/api/posts/").json()
        self.assertEqual(
            [post["id"] for post in data["results"]],
            [str(post.uuid) for post in (friend, own, follow, yesterday)],
        )

    def test_only_admins_post_globally(self):
        response = self.post(visibility="global")
        self.assertEqual(response.status_code, 400)

        set_role(self.anna, Role.ADMIN)
        response = self.post(visibility="global")
        self.assertEqual(response.status_code, 201)

        own = self.post().json()["id"]
        set_role(self.anna, Role.DEFAULT)
        response = self.client.patch(
            f"/api/posts/{own}/", {"visibility": "global"}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_global_post_in_every_feed(self):
        profile = get_or_create_profile(self.anna)
        profile.profile_visibility = "friends"
        profile.save()
        global_post = Post.objects.create(author=self.anna, text="an alle", visibility="global")
        Post.objects.create(author=self.anna, text="nur Freunde", visibility="public")

        self.as_user(self.jonas)
        feed = self.client.get("/api/posts/").json()["results"]
        self.assertEqual([post["id"] for post in feed], [str(global_post.uuid)])
        self.assertEqual(self.visible_ids(), [str(global_post.uuid)])

    def test_guests_see_only_global_posts(self):
        global_post = Post.objects.create(author=self.anna, text="an alle", visibility="global")
        Post.objects.create(author=self.anna, text="öffentlich", visibility="public")
        Post.objects.create(
            author=self.anna, text="verborgen", visibility="global", hidden_at=timezone.now()
        )
        self.client.logout()

        feed = self.client.get("/api/posts/global/").json()["results"]
        self.assertEqual([post["id"] for post in feed], [str(global_post.uuid)])
        self.assertFalse(feed[0]["liked"])
        self.assertFalse(feed[0]["can_report"])
        self.assertEqual(self.client.get("/api/posts/").status_code, 403)

    def test_repost_reaches_followers_of_reposter(self):
        post = Post.objects.create(author=self.eve, text="teilen")
        Post.objects.filter(pk=post.pk).update(created_at=timezone.now() - timedelta(days=3))
        Follow.objects.create(follower=self.jonas, following=self.anna)
        newer = Post.objects.create(author=self.anna, text="heute")

        self.as_user(self.jonas)
        self.assertEqual(
            [p["id"] for p in self.client.get("/api/posts/").json()["results"]], [str(newer.uuid)]
        )

        self.as_user(self.anna)
        response = self.client.post(f"/api/posts/{post.uuid}/repost/")
        self.assertEqual(response.json(), {"reposted": True, "reposter": None})

        self.as_user(self.jonas)
        feed = self.client.get("/api/posts/").json()["results"]
        self.assertEqual([p["id"] for p in feed], [str(post.uuid), str(newer.uuid)])
        self.assertEqual(feed[0]["reposter"], "anna")
        self.assertFalse(feed[0]["reposted"])

        self.as_user(self.anna)
        self.client.delete(f"/api/posts/{post.uuid}/repost/")
        self.as_user(self.jonas)
        self.assertEqual(len(self.client.get("/api/posts/").json()["results"]), 1)

    def test_latest_repost_moves_post_up(self):
        mia = User.objects.create(username="mia")
        Follow.objects.create(follower=self.jonas, following=self.anna)
        Follow.objects.create(follower=self.jonas, following=mia)
        shared = Post.objects.create(author=self.eve, text="geteilt")
        Repost.objects.create(user=self.anna, post=shared)
        newer = Post.objects.create(author=self.anna, text="neuer")

        self.as_user(self.jonas)
        ids = [p["id"] for p in self.client.get("/api/posts/").json()["results"]]
        self.assertEqual(ids, [str(newer.uuid), str(shared.uuid)])

        Repost.objects.create(user=mia, post=shared)
        feed = self.client.get("/api/posts/").json()["results"]
        self.assertEqual([p["id"] for p in feed], [str(shared.uuid), str(newer.uuid)])
        self.assertEqual(feed[0]["reposter"], "mia")

    def test_cannot_repost_own_or_invisible_post(self):
        own = Post.objects.create(author=self.anna, text="meins")
        self.assertEqual(self.client.post(f"/api/posts/{own.uuid}/repost/").status_code, 400)
        hidden = Post.objects.create(author=self.eve, text="geheim", visibility="friends")
        self.assertEqual(self.client.post(f"/api/posts/{hidden.uuid}/repost/").status_code, 404)

    def test_repost_does_not_widen_audience(self):
        post = Post.objects.create(author=self.eve, text="Freunde", visibility="friends")
        self.befriend(self.anna, self.eve)
        self.client.post(f"/api/posts/{post.uuid}/repost/")
        Follow.objects.create(follower=self.jonas, following=self.anna)
        self.as_user(self.jonas)
        self.assertEqual(self.client.get("/api/posts/").json()["results"], [])

    def test_feed_pages(self):
        Follow.objects.create(follower=self.jonas, following=self.anna)
        Post.objects.bulk_create(Post(author=self.anna, text=str(i)) for i in range(30))
        self.as_user(self.jonas)
        first = self.client.get("/api/posts/").json()
        second = self.client.get(first["next"]).json()
        self.assertEqual((len(first["results"]), len(second["results"])), (25, 5))

    def test_only_author_deletes_post_and_files(self):
        data = self.post(images=[image_upload(), image_upload()]).json()
        post = Post.objects.get(uuid=data["id"])
        files = [image.file for image in post.images.all()] + [post.thumbnail]

        self.as_user(self.jonas)
        self.assertEqual(self.client.delete(f"/api/posts/{post.uuid}/").status_code, 403)
        self.as_user(self.anna)
        self.assertEqual(self.client.delete(f"/api/posts/{post.uuid}/").status_code, 204)
        self.assertFalse(any(file.storage.exists(file.name) for file in files))

    def test_likes(self):
        post = self.post().json()["id"]
        self.as_user(self.jonas)
        self.client.post(f"/api/posts/{post}/like/")
        response = self.client.post(f"/api/posts/{post}/like/")
        self.assertEqual(response.json(), {"liked": True, "like_count": "1"})
        data = self.client.get(f"/api/posts/{post}/").json()
        self.assertEqual((data["like_count"], data["liked"]), ("1", True))
        self.client.delete(f"/api/posts/{post}/like/")
        self.assertEqual(self.client.get(f"/api/posts/{post}/").json()["like_count"], "0")

    def test_comments(self):
        post = self.post().json()["id"]
        self.as_user(self.jonas)
        comment = self.client.post(f"/api/posts/{post}/comments/", {"text": "Schön"}).json()
        self.assertTrue(comment["can_delete"])
        self.assertEqual(self.client.get(f"/api/posts/{post}/").json()["comment_count"], 1)

        self.as_user(self.eve)
        self.assertFalse(
            self.client.get(f"/api/posts/{post}/comments/").json()["results"][0]["can_delete"]
        )
        self.assertEqual(self.client.delete(f"/api/comments/{comment['id']}/").status_code, 403)
        self.as_user(self.anna)
        self.assertEqual(self.client.delete(f"/api/comments/{comment['id']}/").status_code, 403)
        self.as_user(self.jonas)
        self.assertEqual(self.client.delete(f"/api/comments/{comment['id']}/").status_code, 200)

    def vote(self, comment, value):
        return self.client.put(
            f"/api/comments/{comment}/vote/", {"value": value}, content_type="application/json"
        )

    def test_comment_votes(self):
        post = self.post().json()["id"]
        comment = self.client.post(f"/api/posts/{post}/comments/", {"text": "Hallo"}).json()
        self.assertEqual((comment["can_vote"], comment["score"]), (False, "0"))
        self.assertEqual(self.vote(comment["id"], 1).status_code, 403)

        self.as_user(self.jonas)
        self.assertEqual(self.vote(comment["id"], 1).json(), {"score": "1", "my_vote": 1})
        self.assertEqual(self.vote(comment["id"], -1).json(), {"score": "-1", "my_vote": -1})
        self.assertEqual(self.vote(comment["id"], 2).status_code, 400)
        self.as_user(self.eve)
        self.assertEqual(self.vote(comment["id"], -1).json(), {"score": "-2", "my_vote": -1})
        self.assertEqual(self.vote(comment["id"], 0).json(), {"score": "-1", "my_vote": 0})

        data = self.client.get(f"/api/posts/{post}/comments/").json()["results"][0]
        self.assertEqual((data["score"], data["my_vote"], data["can_vote"]), ("-1", 0, True))

    def reply(self, comment, text):
        return self.client.post(f"/api/comments/{comment}/replies/", {"text": text}).json()

    def test_comment_replies(self):
        post = self.post().json()["id"]
        self.as_user(self.jonas)
        root = self.client.post(f"/api/posts/{post}/comments/", {"text": "Erster"}).json()["id"]
        first = self.reply(root, "Antwort 1")
        last = self.reply(root, "Antwort 2")
        nested = self.reply(last["id"], "Tiefer")
        self.assertEqual((last["parent_id"], last["reply_to"]), (root, "jonas"))

        comments = self.client.get(f"/api/posts/{post}/comments/").json()["results"]
        self.assertEqual([comment["id"] for comment in comments], [root])
        self.assertEqual(comments[0]["reply_count"], 2)
        self.assertEqual(comments[0]["latest_reply"]["id"], last["id"])
        self.assertEqual(comments[0]["latest_reply"]["reply_count"], 1)
        self.assertEqual(self.client.get(f"/api/posts/{post}/").json()["comment_count"], 1)

        replies = self.client.get(f"/api/comments/{root}/replies/").json()["results"]
        self.assertEqual([reply["id"] for reply in replies], [first["id"], last["id"]])

        thread = self.client.get(f"/api/comments/{nested['id']}/").json()
        self.assertEqual([item["id"] for item in thread["ancestors"]], [root, last["id"]])
        self.assertEqual(thread["post"]["id"], post)

        data = self.client.delete(f"/api/comments/{last['id']}/").json()
        self.assertFalse(Comment.objects.filter(uuid=nested["id"]).exists())
        self.assertEqual(data["parent"]["latest_reply"]["id"], first["id"])
        self.assertEqual((data["parent"]["reply_count"], data["comment_count"]), (1, 1))

    def test_post_author_is_marked(self):
        post = self.post().json()["id"]
        self.as_user(self.jonas)
        root = self.client.post(f"/api/posts/{post}/comments/", {"text": "Frage"}).json()
        self.assertFalse(root["is_post_author"])
        self.as_user(self.anna)
        self.assertTrue(self.reply(root["id"], "Antwort")["is_post_author"])

    def test_replies_need_visible_comment(self):
        hidden = Post.objects.create(author=self.eve, text="geheim", visibility="friends")
        comment = Comment.objects.create(post=hidden, author=self.eve, text="x")
        response = self.client.post(f"/api/comments/{comment.uuid}/replies/", {"text": "y"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.client.get(f"/api/comments/{comment.uuid}/").status_code, 404)

    def test_activities_separate_posts_and_visible_comments(self):
        own = self.post().json()["id"]
        hidden = Post.objects.create(author=self.eve, text="geheim", visibility="friends")
        public = Post.objects.create(author=self.eve, text="offen")
        Comment.objects.create(post=hidden, author=self.anna, text="versteckt")
        comment = Comment.objects.create(post=public, author=self.anna, text="Schön")

        self.as_user(self.jonas)
        data = self.client.get("/api/posts/users/anna/activities/").json()
        self.assertEqual([(item["type"], item["id"]) for item in data["results"]], [("post", own)])
        self.assertIsNone(data["next"])

        data = self.client.get("/api/posts/users/anna/activities/?comments=1").json()
        self.assertEqual(
            [(item["type"], item["id"]) for item in data["results"]],
            [("comment", str(comment.uuid))],
        )
        self.assertEqual(data["results"][0]["post"]["id"], str(public.uuid))
        self.assertIsNone(data["next"])

    def test_activities_pages(self):
        posts = Post.objects.bulk_create(Post(author=self.anna, text=str(i)) for i in range(30))
        for post in posts:
            Comment.objects.create(post=post, author=self.anna, text="x")
        url = "/api/posts/users/anna/activities/?comments=1"
        first = self.client.get(url).json()
        second = self.client.get(f"{url}&{first['next'][1:]}").json()
        self.assertEqual((len(first["results"]), len(second["results"])), (25, 5))
        types = {item["type"] for item in first["results"] + second["results"]}
        self.assertEqual(types, {"comment"})

    def test_saved_posts_and_folders(self):
        first, second = self.post().json()["id"], self.post().json()["id"]
        self.as_user(self.jonas)
        folder = self.client.post("/api/posts/folders/", {"name": "Rezepte"}).json()
        self.assertEqual(
            self.client.post("/api/posts/folders/", {"name": "Rezepte"}).status_code, 400
        )

        self.client.put(
            f"/api/posts/{first}/save/", {"folder": folder["id"]}, content_type="application/json"
        )
        self.client.put(f"/api/posts/{second}/save/", {}, content_type="application/json")

        def saved(query=""):
            return [p["id"] for p in self.client.get(f"/api/posts/saved/{query}").json()["results"]]

        self.assertEqual(saved(), [second, first])
        self.assertEqual(saved(f"?folder={folder['id']}"), [first])
        self.assertEqual(saved("?folder=none"), [second])

        self.client.delete(f"/api/posts/folders/{folder['id']}/")
        self.assertEqual(saved("?folder=none"), [second, first])
        self.client.delete(f"/api/posts/{second}/save/")
        self.assertEqual(saved(), [first])

    def test_foreign_folder_is_rejected(self):
        post = self.post().json()["id"]
        folder = SavedFolder.objects.create(owner=self.jonas, name="Fremd")
        response = self.client.put(
            f"/api/posts/{post}/save/", {"folder": folder.pk}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 404)

    def test_groups(self):
        response = self.client.post(
            "/api/posts/groups/",
            {"name": "Familie", "members": ["jonas"]},
            content_type="application/json",
        )
        group = response.json()
        self.assertEqual(group["members"], ["jonas"])
        response = self.client.patch(
            f"/api/posts/groups/{group['id']}/",
            {"members": ["anna"]},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

        self.as_user(self.jonas)
        self.assertEqual(self.client.get("/api/posts/groups/").json(), [])
        self.assertEqual(self.client.delete(f"/api/posts/groups/{group['id']}/").status_code, 404)


def video_upload(seconds=2, width=1080, height=1920):
    with tempfile.NamedTemporaryFile(suffix=".mov") as file:
        subprocess.run(
            [
                *("ffmpeg", "-v", "error", "-y"),
                *("-f", "lavfi", "-i", f"testsrc=size={width}x{height}:rate=30"),
                *("-f", "lavfi", "-i", "sine"),
                *("-t", str(seconds), "-pix_fmt", "yuv420p", file.name),
            ],
            check=True,
        )
        data = Path(file.name).read_bytes()
    return SimpleUploadedFile("clip.mov", data, content_type="video/quicktime")


@override_settings(MEDIA_ROOT=MEDIA)
class VideoTests(TestCase):
    def setUp(self):
        self.anna = User.objects.create(username="anna")
        self.jonas = User.objects.create(username="jonas")
        self.client.force_login(self.anna)

    def post(self, **data):
        return self.client.post("/api/posts/", {"text": "Clip", **data})

    def process(self):
        call_command("process_videos", "--once", stdout=io.StringIO(), stderr=io.StringIO())

    def ids(self, query=""):
        data = self.client.get(f"/api/posts/users/anna/{query}").json()
        return [post["id"] for post in data["results"]]

    def test_video_is_transcoded_in_background(self):
        data = self.post(video=video_upload()).json()
        self.assertEqual((data["video_status"], data["video"]), ("processing", None))
        self.assertEqual(self.ids(), [data["id"]])
        self.assertEqual(self.ids("?media=1"), [])
        self.client.force_login(self.jonas)
        self.assertEqual(self.ids(), [])

        self.process()
        post = Post.objects.get()
        self.assertFalse(post.video_upload)
        self.assertEqual((post.image_width, post.image_height), (720, 1280))

        data = self.client.get(f"/api/posts/{data['id']}/").json()
        self.assertEqual(data["video_status"], "ready")
        self.assertEqual(self.ids("?videos=1"), [data["id"]])
        self.assertEqual(self.ids("?images=1"), [])
        self.assertEqual(self.ids("?media=1"), [data["id"]])

        response = self.client.get(data["video"])
        self.assertEqual(response["Content-Type"], "video/mp4")
        video = b"".join(response.streaming_content)
        self.assertEqual(len(video), post.video.size)

        response = self.client.get(data["video"], HTTP_RANGE="bytes=100-199")
        self.assertEqual(response.status_code, 206)
        self.assertEqual(response["Content-Range"], f"bytes 100-199/{len(video)}")
        self.assertEqual(b"".join(response.streaming_content), video[100:200])
        response = self.client.get(data["video"], HTTP_RANGE="bytes=-10")
        self.assertEqual(b"".join(response.streaming_content), video[-10:])
        response = self.client.get(data["video"], HTTP_RANGE=f"bytes={len(video)}-")
        self.assertEqual(response.status_code, 416)

    def test_invalid_videos_are_rejected(self):
        self.assertEqual(self.post(video=video_upload(seconds=62)).status_code, 400)
        upload = SimpleUploadedFile("x.mp4", b"no video", content_type="video/mp4")
        self.assertEqual(self.post(video=upload).status_code, 400)
        response = self.post(video=video_upload(), images=[image_upload(10, 10)])
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Post.objects.exists())

    def test_failed_video_stays_private(self):
        data = self.post(video=video_upload()).json()
        post = Post.objects.get()
        Path(post.video_upload.path).write_bytes(b"broken")
        self.process()
        post.refresh_from_db()
        self.assertEqual(post.video_status, Post.VideoStatus.FAILED)
        self.assertFalse(post.video_upload)
        self.client.force_login(self.jonas)
        self.assertEqual(self.client.get(f"/api/posts/{data['id']}/").status_code, 404)

    def test_deleting_post_removes_video_files(self):
        data = self.post(video=video_upload()).json()
        self.process()
        path = Path(Post.objects.get().video.path)
        self.assertTrue(path.exists())
        self.client.delete(f"/api/posts/{data['id']}/")
        self.assertFalse(path.exists())

    def test_reel_feed_shows_followed_videos_newest_first(self):
        first = self.post(video=video_upload()).json()["id"]
        second = self.post(video=video_upload()).json()["id"]
        self.post()
        self.process()

        self.client.force_login(self.jonas)
        self.assertEqual(self.client.get("/api/posts/reels/").json()["results"], [])
        Follow.objects.create(follower=self.jonas, following=self.anna)
        reels = self.client.get("/api/posts/reels/").json()["results"]
        self.assertEqual([reel["id"] for reel in reels], [second, first])

    def test_reels_continue_from_opened_reel(self):
        first = self.post(video=video_upload()).json()["id"]
        second = self.post(video=video_upload()).json()["id"]
        third = self.post(video=video_upload()).json()["id"]
        self.process()
        self.assertEqual(self.ids(f"?videos=1&from={second}"), [second, first])
        self.assertEqual(self.ids(f"?videos=1&from={third}"), [third, second, first])
        self.assertEqual(self.ids("?videos=1&from=kaputt"), [third, second, first])


@override_settings(MEDIA_ROOT=MEDIA)
class HashtagTests(TestCase):
    def setUp(self):
        self.anna = User.objects.create(username="anna")
        self.jonas = User.objects.create(username="jonas")
        self.client.force_login(self.anna)

    def post(self, text, **data):
        return self.client.post("/api/posts/", {"text": text, **data}).json()["id"]

    def test_hashtags_are_extracted_from_text(self):
        self.post("Ferien in #Zürich und #zürich, #Berg-Tour ##double")
        post = Post.objects.get()
        self.assertEqual(sorted(post.hashtags.values_list("name", flat=True)), ["berg", "zürich"])

    def test_search_finds_hashtags_with_visible_posts(self):
        self.post("#zürich")
        self.post("#zug", visibility="friends")
        self.client.force_login(self.jonas)
        results = self.client.get("/api/posts/hashtags/", {"q": "#z"}).json()
        self.assertEqual(results, [{"name": "zürich", "post_count": "1", "following": False}])

    def test_followed_hashtags_appear_in_feeds(self):
        text_post = self.post("Hallo #zürich")
        reel = self.post("Clip #zürich", video=video_upload())
        call_command("process_videos", "--once", stdout=io.StringIO())
        self.post("Anderes #bern")

        self.client.force_login(self.jonas)
        self.assertEqual(self.client.get("/api/posts/").json()["results"], [])
        response = self.client.put("/api/posts/hashtags/Zürich/follow/")
        self.assertTrue(response.json()["following"])

        feed = self.client.get("/api/posts/").json()["results"]
        self.assertEqual({post["id"] for post in feed}, {text_post, reel})
        reels = self.client.get("/api/posts/reels/").json()["results"]
        self.assertEqual([post["id"] for post in reels], [reel])
        tagged = self.client.get("/api/posts/hashtags/zürich/posts/").json()["results"]
        self.assertEqual([post["id"] for post in tagged], [reel, text_post])

        self.assertFalse(
            self.client.delete("/api/posts/hashtags/zürich/follow/").json()["following"]
        )
        self.assertEqual(self.client.get("/api/posts/").json()["results"], [])
        self.assertEqual(self.client.get("/api/posts/hashtags/unbekannt/").status_code, 404)


@override_settings(MEDIA_ROOT=MEDIA)
class StoryTests(TestCase):
    def setUp(self):
        self.jonas = User.objects.create(username="jonas")
        self.anna = User.objects.create(username="anna")
        self.client.force_login(self.anna)

    def create(self, **data):
        return self.client.post("/api/stories/", {"image": image_upload(), **data})

    def stories_for(self, viewer):
        self.client.force_login(viewer)
        return self.client.get("/api/social/profiles/anna/").json()["stories"]

    def test_create_and_view_stories(self):
        response = self.create(text="Hallo Welt")
        self.assertEqual(response.status_code, 201)
        first = response.json()
        self.assertEqual(first["text"], "Hallo Welt")
        self.assertTrue(first["is_own"])
        second = self.create().json()

        seen = self.stories_for(self.jonas)
        self.assertEqual([story["id"] for story in seen], [first["id"], second["id"]])
        self.assertFalse(seen[0]["is_own"])
        image = self.client.get(first["image"])
        self.assertEqual(image["Content-Type"], "image/webp")

    def test_story_expires_after_a_day(self):
        story = self.create().json()
        Story.objects.update(created_at=timezone.now() - timedelta(hours=25))
        self.assertEqual(self.stories_for(self.jonas), [])
        self.assertEqual(self.client.get(story["image"]).status_code, 404)

        self.client.force_login(self.anna)
        self.create()
        call_command("delete_expired_stories", stdout=io.StringIO())
        self.assertEqual(Story.objects.count(), 1)

    def test_story_audience(self):
        self.create(visibility="friends")
        self.assertEqual(self.stories_for(self.jonas), [])
        Friendship.objects.create(user=self.jonas, friend=self.anna)
        self.assertEqual(len(self.stories_for(self.jonas)), 1)

    def test_story_cannot_be_global(self):
        set_role(self.anna, Role.ADMIN)
        self.assertEqual(self.create(visibility="global").status_code, 400)

    def test_like_story(self):
        story = self.create().json()
        self.client.force_login(self.jonas)
        liked = self.client.post(f"/api/stories/{story['id']}/like/").json()
        self.assertTrue(liked["liked"])
        self.assertIsNone(liked["like_count"])

        self.client.force_login(self.anna)
        own = self.stories_for(self.anna)[0]
        self.assertEqual(own["like_count"], "1")

        self.client.force_login(self.jonas)
        unliked = self.client.delete(f"/api/stories/{story['id']}/like/").json()
        self.assertFalse(unliked["liked"])

    def test_post_author_shows_story(self):
        post = Post.objects.create(author=self.anna, text="Hallo")
        self.client.force_login(self.jonas)
        author = self.client.get(f"/api/posts/{post.uuid}/").json()["author"]
        self.assertFalse(author["has_story"])

        Story.objects.create(author=self.anna, image="s.webp", visibility="friends")
        author = self.client.get(f"/api/posts/{post.uuid}/").json()["author"]
        self.assertFalse(author["has_story"])

        Story.objects.create(author=self.anna, image="s.webp")
        author = self.client.get(f"/api/posts/{post.uuid}/").json()["author"]
        self.assertTrue(author["has_story"])

    def test_story_viewers(self):
        story = self.create().json()
        mia = User.objects.create(username="mia")
        for viewer in (self.jonas, mia):
            self.client.force_login(viewer)
            self.client.post(f"/api/stories/{story['id']}/view/")
        self.client.post(f"/api/stories/{story['id']}/like/")

        viewers_url = f"/api/stories/{story['id']}/viewers/"
        self.assertEqual(self.client.get(viewers_url).status_code, 404)

        self.client.force_login(self.anna)
        self.client.post(f"/api/stories/{story['id']}/view/")
        self.assertEqual(self.stories_for(self.anna)[0]["view_count"], "2")
        viewers = self.client.get(viewers_url).json()["results"]
        self.assertEqual(
            [(user["username"], user["liked"]) for user in viewers],
            [("mia", True), ("jonas", False)],
        )

    def test_expired_story_leaves_no_trace(self):
        story = self.create().json()
        self.client.force_login(self.jonas)
        self.client.post(f"/api/stories/{story['id']}/like/")
        Story.objects.update(created_at=timezone.now() - timedelta(hours=25))

        self.client.force_login(self.anna)
        response = self.client.get(f"/api/stories/{story['id']}/viewers/")
        self.assertEqual(response.status_code, 404)

        call_command("delete_expired_stories", stdout=io.StringIO())
        self.assertFalse(StoryLike.objects.exists())
        self.assertFalse(StoryView.objects.exists())

    def test_story_seen(self):
        story = self.create().json()
        self.assertFalse(self.stories_for(self.jonas)[0]["seen"])
        post = Post.objects.create(author=self.anna, text="Hallo")
        author = self.client.get(f"/api/posts/{post.uuid}/").json()["author"]
        self.assertEqual((author["has_story"], author["story_seen"]), (True, False))

        self.client.post(f"/api/stories/{story['id']}/view/")
        self.assertTrue(self.stories_for(self.jonas)[0]["seen"])
        author = self.client.get(f"/api/posts/{post.uuid}/").json()["author"]
        self.assertEqual((author["has_story"], author["story_seen"]), (True, True))

    def test_only_author_deletes_story(self):
        story = self.create().json()
        self.client.force_login(self.jonas)
        self.assertEqual(self.client.delete(f"/api/stories/{story['id']}/").status_code, 404)
        self.client.force_login(self.anna)
        self.assertEqual(self.client.delete(f"/api/stories/{story['id']}/").status_code, 204)
        self.assertFalse(Story.objects.exists())


@override_settings(MEDIA_ROOT=MEDIA)
class AlbumTests(TestCase):
    def setUp(self):
        self.anna = User.objects.create(username="anna")
        self.jonas = User.objects.create(username="jonas")
        self.client.force_login(self.anna)

    def feed(self, **data):
        data = {"text": "Bild", "images": [image_upload(10, 10)], **data}
        return self.client.post("/api/posts/", data).json()["id"]

    def album(self, name="Ferien", **data):
        response = self.client.post("/api/albums/", {"name": name, **data})
        self.assertEqual(response.status_code, 201)
        return response.json()

    def albums(self):
        return [a["name"] for a in self.client.get("/api/posts/users/anna/albums/").json()]

    def covers(self):
        return [a["cover"] for a in self.client.get("/api/posts/users/anna/albums/").json()]

    def send(self, method, url, data=None):
        return getattr(self.client, method)(url, data, content_type="application/json")

    def add(self, album, *entries):
        return self.send("post", f"/api/albums/{album['id']}/entries/", {"entries": entries})

    def detail(self, album):
        return self.client.get(f"/api/albums/{album['id']}/").json()

    def posts(self, album):
        return [entry["post"]["id"] for entry in self.detail(album)["entries"]]

    def test_existing_posts_are_added_with_optional_dates(self):
        album = self.album()
        self.assertTrue(album["is_own"])
        self.assertEqual(album["entries"], [])
        self.assertIsNone(album["cover"])

        beach, city = self.feed(), self.feed()
        response = self.add(
            album, {"post": beach, "date": "2003-05-01", "title": "Strand"}, {"post": city}
        )
        self.assertEqual(response.status_code, 201)
        entries = response.json()["entries"]
        self.assertEqual([e["post"]["id"] for e in entries], [beach, city])
        self.assertEqual((entries[0]["date"], entries[0]["title"]), ("2003-05-01", "Strand"))
        self.assertEqual((entries[1]["date"], entries[1]["title"]), (None, ""))

        self.assertEqual(self.add(album, {"post": beach}).status_code, 400)
        later = self.feed()
        self.assertEqual(self.add(album, {"post": later}, {"post": later}).status_code, 400)
        self.assertEqual(self.posts(album), [beach, city])

    def test_new_albums_come_first_and_order_is_draggable(self):
        ferien, familie = self.album("Ferien"), self.album("Familie")
        self.assertEqual(self.albums(), ["Familie", "Ferien"])

        order = {"albums": [ferien["id"], familie["id"]]}
        response = self.send("put", "/api/albums/order/", order)
        self.assertEqual([a["name"] for a in response.json()], ["Ferien", "Familie"])
        self.album("Neu")
        self.assertEqual(self.albums(), ["Neu", "Ferien", "Familie"])

        partial = {"albums": [ferien["id"]]}
        self.assertEqual(self.send("put", "/api/albums/order/", partial).status_code, 400)
        self.client.force_login(self.jonas)
        self.assertEqual(self.send("put", "/api/albums/order/", order).status_code, 400)

    def test_timeline_is_sorted_by_date_with_undated_posts_last(self):
        album = self.album()
        undated, summer, spring = self.feed(), self.feed(), self.feed()
        self.add(album, {"post": undated}, {"post": summer, "date": "2019-07-14"})
        self.add(album, {"post": spring, "date": "2019-03-01"})
        self.assertEqual(self.posts(album), [spring, summer, undated])

        entry = self.detail(album)["entries"][2]
        url = f"/api/album-entries/{entry['id']}/"
        self.send("patch", url, {"date": "2001-01-01"})
        self.assertEqual(self.posts(album), [undated, spring, summer])

    def test_entry_date_can_be_set_and_cleared(self):
        album = self.album()
        entry = self.add(album, {"post": self.feed()}).json()["entries"][0]
        url = f"/api/album-entries/{entry['id']}/"
        entry = self.send("patch", url, {"date": "1999-12-31", "title": "Silvester"}).json()
        self.assertEqual(
            (entry["entries"][0]["date"], entry["entries"][0]["title"]), ("1999-12-31", "Silvester")
        )
        entry = self.send("patch", url, {"date": None}).json()
        self.assertIsNone(entry["entries"][0]["date"])

        self.assertEqual(self.client.delete(url).json()["entries"], [])

    def test_only_own_media_posts_can_be_added(self):
        album = self.album()
        text_only = self.client.post("/api/posts/", {"text": "Nur Text"}).json()["id"]
        self.assertEqual(self.add(album, {"post": text_only}).status_code, 400)

        self.client.force_login(self.jonas)
        foreign = self.feed()
        self.client.force_login(self.anna)
        self.assertEqual(self.add(album, {"post": foreign}).status_code, 400)

    def test_others_see_albums_but_cannot_change_them(self):
        album = self.album()
        public, friends = self.feed(), self.feed(visibility="friends")
        self.add(album, {"post": public}, {"post": friends})

        self.client.force_login(self.jonas)
        self.assertFalse(self.detail(album)["is_own"])
        self.assertEqual(self.posts(album), [public])
        url = f"/api/albums/{album['id']}/"
        self.assertEqual(self.send("patch", url, {"name": "X"}).status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.assertEqual(self.add(album, {"post": public}).status_code, 404)
        self.assertTrue(Album.objects.filter(name="Ferien").exists())

    def test_private_profile_hides_albums(self):
        album = self.album()
        profile = get_or_create_profile(self.anna)
        profile.profile_visibility = "friends"
        profile.save()

        self.client.force_login(self.jonas)
        self.assertEqual(self.client.get("/api/posts/users/anna/albums/").status_code, 403)
        self.assertEqual(self.client.get(f"/api/albums/{album['id']}/").status_code, 403)

    def test_cover_is_chosen_from_album_entries(self):
        album = self.album()
        first, second = self.add(album, {"post": self.feed()}, {"post": self.feed()}).json()[
            "entries"
        ]
        url = f"/api/albums/{album['id']}/"

        cover = self.send("patch", url, {"cover": second["id"]}).json()["cover"]
        self.assertEqual(cover, second["post"]["thumbnail"])
        self.assertEqual(self.client.get(cover).status_code, 200)
        self.assertEqual(self.covers(), [cover])

        self.assertIsNone(self.send("patch", url, {"cover": None}).json()["cover"])
        self.send("patch", url, {"cover": first["id"]})
        self.client.delete(f"/api/album-entries/{first['id']}/")
        self.assertIsNone(self.detail(album)["cover"])

    def test_cover_must_belong_to_the_album(self):
        album, other = self.album(), self.album("Familie")
        entry = self.add(other, {"post": self.feed()}).json()["entries"][0]
        url = f"/api/albums/{album['id']}/"
        self.assertEqual(self.send("patch", url, {"cover": entry["id"]}).status_code, 400)
        response = self.client.post("/api/albums/", {"name": "Neu", "cover": entry["id"]})
        self.assertEqual(response.status_code, 400)

    def test_hidden_cover_post_is_not_shown_to_others(self):
        album = self.album()
        entry = self.add(album, {"post": self.feed(visibility="friends")}).json()["entries"][0]
        self.send("patch", f"/api/albums/{album['id']}/", {"cover": entry["id"]})

        self.client.force_login(self.jonas)
        self.assertIsNone(self.detail(album)["cover"])
