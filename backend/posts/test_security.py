import io
import shutil
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from accounts.models import UserProfile, get_or_create_profile
from accounts.roles import Role, set_role
from social.models import Follow, Friendship

from .models import Comment, ContactGroup, Post, PostImage, SavedFolder
from .tests import image_upload, video_upload

User = get_user_model()
MEDIA = tempfile.mkdtemp()
PADDING = "#" + "x" * 3 * 1024 * 1024 + "\n"


def file_upload(name, data, content_type="application/octet-stream"):
    return SimpleUploadedFile(name, data.encode() if isinstance(data, str) else data, content_type)


def image_bytes(format, size=(64, 64), mode="RGB"):
    data = io.BytesIO()
    Image.new(mode, size, "red").save(data, format=format)
    return data.getvalue()


@override_settings(MEDIA_ROOT=MEDIA)
class SecurityTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.anna = User.objects.create(username="anna")
        self.jonas = User.objects.create(username="jonas")
        self.eve = User.objects.create(username="eve")
        self.client.force_login(self.anna)

    def as_user(self, user):
        self.client.force_login(user)

    def create_post(self, **data):
        response = self.client.post("/api/posts/", {"text": "Hallo", **data})
        self.assertEqual(response.status_code, 201, response.content)
        return Post.objects.get(uuid=response.json()["id"])


class PrivateContentTests(SecurityTestCase):
    def setUp(self):
        super().setUp()
        Friendship.objects.create(user=self.anna, friend=self.jonas)
        Friendship.objects.create(user=self.jonas, friend=self.anna)
        self.group = ContactGroup.objects.create(owner=self.anna, name="Familie")
        self.group.members.add(self.jonas)
        self.posts = {
            "friends": self.create_post(visibility="friends", images=[image_upload()]),
            "followers": self.create_post(visibility="followers", images=[image_upload()]),
            "groups": self.create_post(
                visibility="groups", groups=[self.group.pk], images=[image_upload()]
            ),
        }
        Comment.objects.create(post=self.posts["friends"], author=self.anna, text="geheim")

    def private_urls(self, post):
        return [
            f"/api/posts/{post.uuid}/",
            f"/api/posts/{post.uuid}/images/0/",
            f"/api/posts/{post.uuid}/thumbnail/",
            f"/api/posts/{post.uuid}/video/",
            f"/api/posts/{post.uuid}/comments/",
        ]

    def test_strangers_cannot_reach_private_posts_or_media(self):
        self.as_user(self.eve)
        for kind, post in self.posts.items():
            for url in self.private_urls(post):
                with self.subTest(kind=kind, url=url):
                    self.assertEqual(self.client.get(url).status_code, 404)

    def test_strangers_cannot_interact_with_private_posts(self):
        self.as_user(self.eve)
        for kind, post in self.posts.items():
            actions = [
                ("post", f"/api/posts/{post.uuid}/like/", {}),
                ("put", f"/api/posts/{post.uuid}/save/", {}),
                ("post", f"/api/posts/{post.uuid}/comments/", {"text": "hi"}),
                ("post", f"/api/posts/{post.uuid}/report/", {}),
                ("delete", f"/api/posts/{post.uuid}/", {}),
            ]
            for method, url, data in actions:
                with self.subTest(kind=kind, url=url, method=method):
                    response = getattr(self.client, method)(
                        url, data, content_type="application/json"
                    )
                    self.assertEqual(response.status_code, 404)
        self.assertEqual(Comment.objects.filter(author=self.eve).count(), 0)

    def test_private_posts_do_not_leak_through_lists(self):
        self.as_user(self.eve)
        Follow.objects.create(follower=self.eve, following=self.anna)
        hidden = {str(post.uuid) for post in self.posts.values() if post.visibility != "followers"}
        for url in [
            "/api/posts/",
            "/api/posts/users/anna/",
            "/api/posts/reels/",
            "/api/posts/users/anna/activities/",
            "/api/posts/saved/",
        ]:
            with self.subTest(url=url):
                content = self.client.get(url).content.decode()
                for uuid in hidden:
                    self.assertNotIn(uuid, content)

    def test_private_comments_do_not_leak(self):
        comment = Comment.objects.get(text="geheim")
        self.as_user(self.eve)
        for url in [
            f"/api/comments/{comment.uuid}/",
            f"/api/comments/{comment.uuid}/replies/",
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)
        response = self.client.put(
            f"/api/comments/{comment.uuid}/vote/", {"value": 1}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 404)
        self.assertNotIn(
            "geheim", self.client.get("/api/posts/users/anna/activities/").content.decode()
        )

    def test_audience_is_hidden_from_other_viewers(self):
        self.as_user(self.jonas)
        data = self.client.get(f"/api/posts/{self.posts['groups'].uuid}/").json()
        self.assertNotIn("groups", data)
        self.assertNotIn("visibility", data)

    def test_private_profile_hides_public_posts(self):
        profile = get_or_create_profile(self.anna)
        profile.profile_visibility = UserProfile.Visibility.FRIENDS
        profile.save()
        public = self.create_post(visibility="public")
        self.as_user(self.eve)
        self.assertEqual(self.client.get(f"/api/posts/{public.uuid}/").status_code, 404)

    def test_hidden_posts_are_only_visible_to_their_author(self):
        post = self.create_post(visibility="public")
        Post.objects.filter(pk=post.pk).update(hidden_at="2026-01-01T00:00Z")
        self.as_user(self.eve)
        self.assertEqual(self.client.get(f"/api/posts/{post.uuid}/").status_code, 404)

    def test_unfinished_videos_are_only_visible_to_their_author(self):
        post = Post.objects.create(author=self.anna, text="x", video_status="processing")
        self.as_user(self.eve)
        self.assertEqual(self.client.get(f"/api/posts/{post.uuid}/").status_code, 404)
        self.assertEqual(self.client.get(f"/api/posts/{post.uuid}/video/").status_code, 404)

    def test_deactivated_authors_disappear(self):
        post = self.create_post(visibility="public")
        User.objects.filter(pk=self.anna.pk).update(is_active=False)
        self.as_user(self.eve)
        self.assertEqual(self.client.get(f"/api/posts/{post.uuid}/").status_code, 404)

    def test_media_is_never_served_from_a_public_path(self):
        image = PostImage.objects.first()
        self.client.logout()
        for url in [
            f"/media/{image.file.name}",
            f"/{image.file.name}",
            f"/api/posts/{self.posts['friends'].uuid}/images/0/",
        ]:
            with self.subTest(url=url):
                self.assertIn(self.client.get(url).status_code, (403, 404))


class OwnershipTests(SecurityTestCase):
    def setUp(self):
        super().setUp()
        self.post = self.create_post(visibility="public")
        self.comment = Comment.objects.create(post=self.post, author=self.anna, text="mein")
        self.folder = SavedFolder.objects.create(owner=self.anna, name="Privat")
        self.group = ContactGroup.objects.create(owner=self.anna, name="Familie")
        self.group.members.add(self.jonas)
        self.as_user(self.eve)

    def test_cannot_delete_foreign_posts_or_comments(self):
        self.assertEqual(self.client.delete(f"/api/posts/{self.post.uuid}/").status_code, 403)
        self.assertEqual(self.client.delete(f"/api/comments/{self.comment.uuid}/").status_code, 403)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_cannot_touch_foreign_folders(self):
        url = f"/api/posts/folders/{self.folder.pk}/"
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(
            self.client.patch(url, {"name": "x"}, content_type="application/json").status_code,
            404,
        )
        self.assertEqual(self.client.delete(url).status_code, 404)
        response = self.client.put(
            f"/api/posts/{self.post.uuid}/save/",
            {"folder": self.folder.pk},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("Privat", self.client.get("/api/posts/folders/").content.decode())

    def test_cannot_list_saved_posts_of_a_foreign_folder(self):
        self.client.force_login(self.anna)
        self.client.put(
            f"/api/posts/{self.post.uuid}/save/",
            {"folder": self.folder.pk},
            content_type="application/json",
        )
        self.as_user(self.eve)
        response = self.client.get("/api/posts/saved/", {"folder": self.folder.pk})
        self.assertEqual(response.json()["results"], [])

    def test_cannot_touch_foreign_groups(self):
        url = f"/api/posts/groups/{self.group.pk}/"
        self.assertEqual(self.client.get(url).status_code, 404)
        response = self.client.patch(url, {"members": ["eve"]}, content_type="application/json")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.assertEqual(list(self.group.members.values_list("username", flat=True)), ["jonas"])

    def test_cannot_post_to_foreign_groups(self):
        response = self.client.post(
            "/api/posts/", {"text": "x", "visibility": "groups", "groups": [self.group.pk]}
        )
        self.assertEqual(response.status_code, 400)

    def test_cannot_vote_on_own_comment_or_with_odd_values(self):
        for value in [2, -2, 100, "1", 1.5, None, [1], {"$gt": 0}]:
            with self.subTest(value=value):
                response = self.client.put(
                    f"/api/comments/{self.comment.uuid}/vote/",
                    {"value": value},
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 400)
        self.client.force_login(self.anna)
        response = self.client.put(
            f"/api/comments/{self.comment.uuid}/vote/",
            {"value": 1},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_folder_names_are_scoped_per_owner(self):
        response = self.client.post(
            "/api/posts/folders/", {"name": "Privat"}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)


class MassAssignmentTests(SecurityTestCase):
    def test_server_controlled_fields_cannot_be_set(self):
        response = self.client.post(
            "/api/posts/",
            {
                "text": "x",
                "author": self.jonas.pk,
                "uuid": "00000000-0000-0000-0000-000000000000",
                "hidden_at": "2020-01-01T00:00:00Z",
                "created_at": "2000-01-01T00:00:00Z",
                "video_status": "ready",
                "thumbnail": "../../etc/passwd",
                "image_width": 99999,
                "like_count": 1000,
                "is_own": False,
            },
        )
        self.assertEqual(response.status_code, 201)
        post = Post.objects.get(uuid=response.json()["id"])
        self.assertEqual(post.author, self.anna)
        self.assertNotEqual(str(post.uuid), "00000000-0000-0000-0000-000000000000")
        self.assertIsNone(post.hidden_at)
        self.assertGreater(post.created_at.year, 2000)
        self.assertEqual(post.video_status, "")
        self.assertFalse(post.thumbnail)
        self.assertIsNone(post.image_width)

    def test_comment_author_and_post_cannot_be_set(self):
        post = self.create_post(visibility="public")
        other = Post.objects.create(author=self.jonas, text="y")
        response = self.client.post(
            f"/api/posts/{post.uuid}/comments/",
            {"text": "hi", "author": self.jonas.pk, "post": other.pk, "hidden_at": None},
            content_type="application/json",
        )
        comment = Comment.objects.get(uuid=response.json()["id"])
        self.assertEqual((comment.author, comment.post), (self.anna, post))

    def test_comment_length_is_limited(self):
        post = self.create_post(visibility="public")
        response = self.client.post(
            f"/api/posts/{post.uuid}/comments/",
            {"text": "x" * 501},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_visibility_must_be_a_known_value(self):
        for visibility in ["everyone", "admin", "' OR 1=1", "PUBLIC", " public"]:
            with self.subTest(visibility=visibility):
                response = self.client.post("/api/posts/", {"text": "x", "visibility": visibility})
                self.assertEqual(response.status_code, 400)

    def test_hashtags_per_post_are_capped(self):
        text = " ".join(f"#tag{i}" for i in range(100))
        post = self.create_post(text=text[:500])
        self.assertLessEqual(post.hashtags.count(), 30)


class ImageUploadTests(SecurityTestCase):
    def upload(self, *files):
        return self.client.post("/api/posts/", {"text": "x", "images": list(files)})

    def test_rejects_formats_outside_the_allowlist(self):
        for format in ["TIFF", "BMP", "ICO", "PPM", "TGA", "PCX", "SGI", "IM"]:
            with self.subTest(format=format):
                response = self.upload(
                    file_upload(f"x.{format.lower()}", image_bytes(format), "image/png")
                )
                self.assertEqual(response.status_code, 400)
        self.assertFalse(Post.objects.exists())

    def test_accepts_common_formats(self):
        for format in ["JPEG", "PNG", "WEBP", "GIF"]:
            with self.subTest(format=format):
                response = self.upload(file_upload("x", image_bytes(format)))
                self.assertEqual(response.status_code, 201, response.content)

    def test_rejects_svg_with_script(self):
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
        response = self.upload(file_upload("x.svg", svg, "image/svg+xml"))
        self.assertEqual(response.status_code, 400)

    def test_rejects_html_and_scripts_disguised_as_images(self):
        for name, data in [
            ("x.jpg", "<html><script>alert(1)</script></html>"),
            ("x.png", "#!/bin/sh\nrm -rf /"),
            ("x.gif", "GIF89a<script>alert(1)</script>"),
            ("x.jpg", "%!PS-Adobe-3.0 EPSF-3.0\n%%BoundingBox: 0 0 1 1\n"),
            ("x.jpg", ""),
        ]:
            with self.subTest(name=name, data=data[:20]):
                self.assertEqual(
                    self.upload(file_upload(name, data, "image/jpeg")).status_code, 400
                )

    def test_polyglot_payload_is_stripped_by_reencoding(self):
        payload = b"<script>alert(document.cookie)</script>"
        response = self.upload(file_upload("x.jpg", image_bytes("JPEG") + payload, "image/jpeg"))
        self.assertEqual(response.status_code, 201)
        post = Post.objects.get(uuid=response.json()["id"])
        served = b"".join(self.client.get(f"/api/posts/{post.uuid}/images/0/").streaming_content)
        self.assertTrue(served.startswith(b"RIFF"))
        self.assertNotIn(payload, served)

    def test_served_images_have_a_fixed_content_type(self):
        post = Post.objects.get(uuid=self.upload(image_upload()).json()["id"])
        response = self.client.get(f"/api/posts/{post.uuid}/images/0/")
        self.assertEqual(response["Content-Type"], "image/webp")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")

    def test_rejects_decompression_bombs(self):
        data = io.BytesIO()
        Image.new("1", (20000, 20000)).save(data, format="PNG")
        response = self.upload(file_upload("bomb.png", data.getvalue(), "image/png"))
        self.assertEqual(response.status_code, 400)

    def test_upload_names_cannot_traverse_paths(self):
        for name in ["../../../../app/main/settings.py", "/etc/passwd", "..\\..\\x.jpg"]:
            with self.subTest(name=name):
                upload = file_upload(name, image_bytes("JPEG"), "image/jpeg")
                post = Post.objects.get(uuid=self.upload(upload).json()["id"])
                stored = post.images.first().file.name
                self.assertNotIn("..", stored)
                self.assertTrue(stored.endswith(".webp"))
                self.assertTrue(Path(post.images.first().file.path).is_relative_to(MEDIA))

    def test_rejects_too_many_images(self):
        files = [file_upload(f"{i}.jpg", image_bytes("JPEG"), "image/jpeg") for i in range(11)]
        self.assertEqual(self.upload(*files).status_code, 400)

    def test_rejects_images_and_video_together(self):
        response = self.client.post(
            "/api/posts/", {"text": "x", "images": [image_upload()], "video": video_upload(1)}
        )
        self.assertEqual(response.status_code, 400)


class VideoUploadTests(SecurityTestCase):
    def setUp(self):
        super().setUp()
        self.segment = Path(tempfile.mkdtemp()) / "secret.mp4"
        self.segment.write_bytes(video_upload(1).read())
        self.addCleanup(shutil.rmtree, self.segment.parent, True)

    def upload(self, name, data, content_type="video/mp4"):
        return self.client.post(
            "/api/posts/", {"text": "x", "video": file_upload(name, data, content_type)}
        )

    def playlist(self, target):
        return (
            "#EXTM3U\n#EXT-X-TARGETDURATION:1\n"
            f"{PADDING}#EXTINF:1.0,\n{target}\n#EXT-X-ENDLIST\n"
        )

    def assert_rejected(self, response):
        self.assertEqual(response.status_code, 400, response.content)
        self.assertFalse(Post.objects.filter(video_status__in=["processing", "ready"]).exists())

    def test_rejects_hls_playlists_pointing_at_local_files(self):
        for target in [f"file://{self.segment}", str(self.segment)]:
            with self.subTest(target=target):
                self.assert_rejected(self.upload("evil.m3u8", self.playlist(target)))

    def test_rejects_hls_playlists_pointing_at_internal_hosts(self):
        for target in [
            "http://db:5432/x.ts",
            "http://169.254.169.254/latest/meta-data.ts",
            "http://localhost:8000/api/health/x.ts",
            "gopher://localhost:6379/x.ts",
        ]:
            with self.subTest(target=target):
                self.assert_rejected(self.upload("evil.m3u8", self.playlist(target)))

    def test_rejects_concat_scripts(self):
        script = f"ffconcat version 1.0\n{PADDING}file '{self.segment}'\n"
        self.assert_rejected(self.upload("evil.ffconcat", script))
        self.assert_rejected(self.upload("evil.mp4", script))

    def test_rejects_non_video_files(self):
        for name, data in [
            ("x.mp4", "not a video"),
            ("x.mp4", image_bytes("PNG")),
            ("x.mp4", "<script>alert(1)</script>"),
            ("x.mp4", b"\x00" * 1024),
        ]:
            with self.subTest(name=name):
                self.assert_rejected(self.upload(name, data))

    def test_accepts_real_videos(self):
        response = self.client.post("/api/posts/", {"text": "x", "video": video_upload(1)})
        self.assertEqual(response.status_code, 201, response.content)

    def test_rejects_too_long_videos(self):
        response = self.client.post("/api/posts/", {"text": "x", "video": video_upload(62, 64, 64)})
        self.assertEqual(response.status_code, 400)


class VideoRangeTests(SecurityTestCase):
    def setUp(self):
        super().setUp()
        self.post = Post.objects.create(author=self.anna, text="x", video_status="ready")
        self.post.video.save("v.mp4", ContentFile(b"0123456789"), save=True)

    def get(self, range_header):
        return self.client.get(
            f"/api/posts/{self.post.uuid}/video/", headers={"Range": range_header}
        )

    def body(self, response):
        return b"".join(response.streaming_content)

    def test_malformed_ranges_never_crash(self):
        for header in [
            "bytes=abc",
            "bytes=-",
            "bytes=--1",
            "bytes=1-2-3",
            "bytes=0-1,2-3",
            "bits=0-1",
            "bytes=99999999999999999999999-",
            "bytes=-99999999999999999999999",
            "bytes=\x00",
            "bytes= 1-2",
        ]:
            with self.subTest(header=header):
                self.assertLess(self.get(header).status_code, 500)

    def test_ranges_stay_inside_the_file(self):
        self.assertEqual(self.body(self.get("bytes=2-4")), b"234")
        self.assertEqual(self.body(self.get("bytes=8-100")), b"89")
        self.assertEqual(self.body(self.get("bytes=-3")), b"789")
        self.assertEqual(self.body(self.get("bytes=-100")), b"0123456789")
        self.assertEqual(self.get("bytes=10-").status_code, 416)
        self.assertEqual(self.get("bytes=5-2").status_code, 416)


class ModeratorVisibilityTests(SecurityTestCase):
    def test_moderators_only_see_private_posts_once_reported(self):
        post = self.create_post(visibility="friends")
        mod = User.objects.create(username="mod")
        set_role(mod, Role.MODERATOR)
        self.as_user(mod)
        self.assertEqual(self.client.get(f"/api/posts/{post.uuid}/").status_code, 404)
        self.assertEqual(self.client.get(f"/api/moderation/posts/{post.uuid}/").status_code, 404)
