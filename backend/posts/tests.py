import io
import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image

from accounts.models import get_or_create_profile
from social.models import Follow, Friendship

from .models import Comment, ContactGroup, Post, PostCreation, SavedFolder

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

    def test_feed_orders_by_day_with_friends_first(self):
        Follow.objects.create(follower=self.jonas, following=self.anna)
        Follow.objects.create(follower=self.jonas, following=self.eve)
        self.befriend(self.jonas, self.eve)
        yesterday = Post.objects.create(author=self.eve, text="gestern")
        Post.objects.filter(pk=yesterday.pk).update(created_at=timezone.now() - timedelta(days=1))
        friend = Post.objects.create(author=self.eve, text="Freundin")
        follow = Post.objects.create(author=self.anna, text="Folge")
        Post.objects.create(author=self.jonas, text="eigener")
        Post.objects.create(author=User.objects.create(username="mia"), text="fremd")

        self.as_user(self.jonas)
        data = self.client.get("/api/posts/").json()
        self.assertEqual(
            [post["id"] for post in data["results"]],
            [str(post.uuid) for post in (friend, follow, yesterday)],
        )

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

    def test_activities_include_visible_comments(self):
        own = self.post().json()["id"]
        hidden = Post.objects.create(author=self.eve, text="geheim", visibility="friends")
        public = Post.objects.create(author=self.eve, text="offen")
        Comment.objects.create(post=hidden, author=self.anna, text="versteckt")
        comment = Comment.objects.create(post=public, author=self.anna, text="Schön")

        self.as_user(self.jonas)
        data = self.client.get("/api/posts/users/anna/activities/").json()
        self.assertEqual(
            [(item["type"], item["id"]) for item in data["results"]],
            [("comment", str(comment.uuid)), ("post", own)],
        )
        self.assertEqual(data["results"][0]["post"]["id"], str(public.uuid))
        self.assertIsNone(data["next"])

    def test_activities_pages(self):
        posts = Post.objects.bulk_create(Post(author=self.anna, text=str(i)) for i in range(20))
        for post in posts[:10]:
            Comment.objects.create(post=post, author=self.anna, text="x")
        first = self.client.get("/api/posts/users/anna/activities/").json()
        second = self.client.get(f"/api/posts/users/anna/activities/{first['next']}").json()
        self.assertEqual((len(first["results"]), len(second["results"])), (25, 5))

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
