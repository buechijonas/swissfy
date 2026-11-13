import io
import json
import shutil
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image

from swissfy.accounts.models import UserProfile, get_or_create_profile
from swissfy.accounts.roles import Role, set_role
from swissfy.moderation.models import Reason, Suspension, Warning
from swissfy.social.models import Follow, Friendship

from .models import (
    Comment,
    ContactGroup,
    Post,
    PostImage,
    Repost,
    SavedFolder,
    Story,
    StoryLike,
    StoryView,
)
from .tests import image_upload, video_upload

User = get_user_model()
MEDIA = tempfile.mkdtemp()
PADDING = "#" + "x" * 3 * 1024 * 1024 + "\n"


def file_upload(name, data, content_type="application/octet-stream"):
    return SimpleUploadedFile(name, data, content_type)


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
        self.secret = Comment.objects.create(
            post=self.posts["friends"], author=self.anna, text="geheim"
        )

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
        reachable = [
            url
            for post in self.posts.values()
            for url in self.private_urls(post)
            if self.client.get(url).status_code != 404
        ]
        self.assertEqual(reachable, [])

    def interactions(self, post):
        return [
            ("post", f"/api/posts/{post.uuid}/like/", {}),
            ("put", f"/api/posts/{post.uuid}/save/", {}),
            ("post", f"/api/posts/{post.uuid}/comments/", {"text": "hi"}),
            ("post", f"/api/posts/{post.uuid}/report/", {}),
            ("delete", f"/api/posts/{post.uuid}/", {}),
        ]

    def interact(self, method, url, data):
        return self.client.generic(
            method.upper(), url, json.dumps(data), content_type="application/json"
        )

    def test_strangers_cannot_interact_with_private_posts(self):
        self.as_user(self.eve)
        allowed = [
            (method, url)
            for post in self.posts.values()
            for method, url, data in self.interactions(post)
            if self.interact(method, url, data).status_code != 404
        ]
        self.assertEqual(allowed, [])
        self.assertEqual(Comment.objects.filter(author=self.eve).count(), 0)

    def test_private_posts_do_not_leak_through_lists(self):
        self.as_user(self.eve)
        Follow.objects.create(follower=self.eve, following=self.anna)
        hidden = {str(post.uuid) for post in self.posts.values() if post.visibility != "followers"}
        lists = [
            "/api/posts/",
            "/api/posts/users/anna/",
            "/api/posts/reels/",
            "/api/posts/users/anna/activities/",
            "/api/posts/users/anna/activities/?comments=1",
            "/api/posts/saved/",
        ]
        leaks = [
            (url, uuid)
            for url in lists
            for uuid in hidden
            if uuid in self.client.get(url).content.decode()
        ]
        self.assertEqual(leaks, [])

    def test_private_comments_do_not_leak(self):
        comment = self.secret
        self.as_user(self.eve)
        self.assertEqual(self.client.get(f"/api/comments/{comment.uuid}/").status_code, 404)
        replies = self.client.get(f"/api/comments/{comment.uuid}/replies/")
        self.assertEqual(replies.status_code, 404)
        response = self.client.put(
            f"/api/comments/{comment.uuid}/vote/", {"value": 1}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 404)
        self.assertNotIn(
            "geheim",
            self.client.get("/api/posts/users/anna/activities/?comments=1").content.decode(),
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
        paths = [
            f"/media/{image.file.name}",
            f"/{image.file.name}",
            f"/api/posts/{self.posts['friends'].uuid}/images/0/",
        ]
        served = [path for path in paths if self.client.get(path).status_code not in (403, 404)]
        self.assertEqual(served, [])


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

    def vote(self, value):
        return self.client.put(
            f"/api/comments/{self.comment.uuid}/vote/",
            {"value": value},
            content_type="application/json",
        )

    def test_cannot_vote_on_own_comment_or_with_odd_values(self):
        odd_values = [2, -2, 100, "1", 1.5, None, [1], {"$gt": 0}]
        accepted = [value for value in odd_values if self.vote(value).status_code != 400]
        self.assertEqual(accepted, [])
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
        unknown = ["everyone", "admin", "' OR 1=1", "PUBLIC", " public"]
        accepted = [
            visibility
            for visibility in unknown
            if self.client.post("/api/posts/", {"text": "x", "visibility": visibility}).status_code
            != 400
        ]
        self.assertEqual(accepted, [])

    def test_hashtags_per_post_are_capped(self):
        text = " ".join(f"#tag{i}" for i in range(100))
        post = self.create_post(text=text[:500])
        self.assertLessEqual(post.hashtags.count(), 30)


class ImageUploadTests(SecurityTestCase):
    def upload(self, *files):
        return self.client.post("/api/posts/", {"text": "x", "images": list(files)})

    def upload_format(self, format, content_type="image/png"):
        return self.upload(file_upload(f"x.{format.lower()}", image_bytes(format), content_type))

    def test_rejects_formats_outside_the_allowlist(self):
        exotic = ["TIFF", "BMP", "ICO", "PPM", "TGA", "PCX", "SGI", "IM"]
        accepted = [format for format in exotic if self.upload_format(format).status_code != 400]
        self.assertEqual(accepted, [])
        self.assertFalse(Post.objects.exists())

    def test_accepts_common_formats(self):
        common = ["JPEG", "PNG", "WEBP", "GIF"]
        rejected = [
            format
            for format in common
            if self.upload(file_upload("x", image_bytes(format))).status_code != 201
        ]
        self.assertEqual(rejected, [])

    def test_rejects_svg_with_script(self):
        svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
        response = self.upload(file_upload("x.svg", svg, "image/svg+xml"))
        self.assertEqual(response.status_code, 400)

    def test_rejects_html_and_scripts_disguised_as_images(self):
        disguised = [
            ("x.jpg", b"<html><script>alert(1)</script></html>"),
            ("x.png", b"#!/bin/sh\nrm -rf /"),
            ("x.gif", b"GIF89a<script>alert(1)</script>"),
            ("x.jpg", b"%!PS-Adobe-3.0 EPSF-3.0\n%%BoundingBox: 0 0 1 1\n"),
            ("x.jpg", b""),
        ]
        accepted = [
            (name, data[:20])
            for name, data in disguised
            if self.upload(file_upload(name, data, "image/jpeg")).status_code != 400
        ]
        self.assertEqual(accepted, [])

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

    def assert_upload_stays_in_media(self, name):
        upload = file_upload(name, image_bytes("JPEG"), "image/jpeg")
        post = Post.objects.get(uuid=self.upload(upload).json()["id"])
        stored = post.images.first().file
        self.assertNotIn("..", stored.name)
        self.assertTrue(stored.name.endswith(".webp"))
        self.assertTrue(Path(stored.path).is_relative_to(MEDIA))

    def test_relative_upload_names_cannot_traverse_paths(self):
        self.assert_upload_stays_in_media("../../../../app/main/settings.py")

    def test_absolute_upload_names_cannot_escape_media(self):
        self.assert_upload_stays_in_media("/etc/passwd")

    def test_windows_upload_names_cannot_traverse_paths(self):
        self.assert_upload_stays_in_media("..\\..\\x.jpg")

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
        ).encode()

    def assert_rejected(self, response):
        self.assertEqual(response.status_code, 400, response.content)
        self.assertFalse(Post.objects.filter(video_status__in=["processing", "ready"]).exists())

    def accepts_playlist(self, target):
        return self.upload("evil.m3u8", self.playlist(target)).status_code != 400

    def test_rejects_hls_playlists_pointing_at_file_urls(self):
        self.assert_rejected(self.upload("evil.m3u8", self.playlist(f"file://{self.segment}")))

    def test_rejects_hls_playlists_pointing_at_local_paths(self):
        self.assert_rejected(self.upload("evil.m3u8", self.playlist(str(self.segment))))

    def test_rejects_hls_playlists_pointing_at_internal_hosts(self):
        internal = [
            "http://db:5432/x.ts",
            "http://169.254.169.254/latest/meta-data.ts",
            "http://localhost:8000/api/health/x.ts",
            "gopher://localhost:6379/x.ts",
        ]
        accepted = [target for target in internal if self.accepts_playlist(target)]
        self.assertEqual(accepted, [])
        self.assertFalse(Post.objects.filter(video_status__in=["processing", "ready"]).exists())

    def test_rejects_concat_scripts(self):
        script = f"ffconcat version 1.0\n{PADDING}file '{self.segment}'\n".encode()
        self.assert_rejected(self.upload("evil.ffconcat", script))
        self.assert_rejected(self.upload("evil.mp4", script))

    def test_rejects_text_as_video(self):
        self.assert_rejected(self.upload("x.mp4", b"not a video"))

    def test_rejects_image_as_video(self):
        self.assert_rejected(self.upload("x.mp4", image_bytes("PNG")))

    def test_rejects_script_as_video(self):
        self.assert_rejected(self.upload("x.mp4", b"<script>alert(1)</script>"))

    def test_rejects_null_bytes_as_video(self):
        self.assert_rejected(self.upload("x.mp4", b"\x00" * 1024))

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
        malformed = [
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
        ]
        crashing = [header for header in malformed if self.get(header).status_code >= 500]
        self.assertEqual(crashing, [])

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


class StorySecurityTests(SecurityTestCase):
    def create_story(self, **data):
        response = self.client.post("/api/stories/", {"image": image_upload(), **data})
        self.assertEqual(response.status_code, 201, response.content)
        return Story.objects.get(uuid=response.json()["id"])

    def test_server_controlled_fields_cannot_be_set(self):
        self.client.post(
            "/api/stories/",
            {
                "image": image_upload(),
                "author": self.eve.pk,
                "created_at": "2000-01-01T00:00:00Z",
                "uuid": "00000000-0000-0000-0000-000000000000",
            },
        )
        story = Story.objects.get()
        self.assertEqual(story.author, self.anna)
        self.assertGreater(story.created_at.year, 2000)
        self.assertNotEqual(str(story.uuid), "00000000-0000-0000-0000-000000000000")

    def assert_story_rejected(self, data):
        self.assertEqual(self.client.post("/api/stories/", data).status_code, 400)
        self.assertFalse(Story.objects.exists())

    def test_story_without_image_is_rejected(self):
        self.assert_story_rejected({"text": "Hallo"})

    def test_story_with_html_image_is_rejected(self):
        upload = file_upload("x.png", b"<script>alert(1)</script>", "image/png")
        self.assert_story_rejected({"image": upload})

    def test_story_with_svg_image_is_rejected(self):
        upload = file_upload("x.svg", b"<svg onload=alert(1)/>", "image/svg+xml")
        self.assert_story_rejected({"image": upload})

    def test_story_text_length_is_limited(self):
        self.assert_story_rejected({"image": image_upload(), "text": "x" * 201})

    def test_story_visibility_must_be_known(self):
        self.assert_story_rejected({"image": image_upload(), "visibility": "everyone"})

    def test_story_for_groups_needs_a_group(self):
        self.assert_story_rejected({"image": image_upload(), "visibility": "groups"})

    def test_cannot_share_story_with_foreign_groups(self):
        foreign = ContactGroup.objects.create(owner=self.eve, name="Fremd")
        response = self.client.post(
            "/api/stories/",
            {"image": image_upload(), "visibility": "groups", "groups": [foreign.pk]},
        )
        self.assertEqual(response.status_code, 400)

    def test_strangers_cannot_reach_private_stories(self):
        story = self.create_story(visibility="friends")
        self.as_user(self.eve)
        actions = [
            ("get", "image/"),
            ("post", "view/"),
            ("post", "like/"),
            ("delete", "like/"),
            ("get", "viewers/"),
            ("delete", ""),
        ]
        reachable = [
            (method, path)
            for method, path in actions
            if self.client.generic(method.upper(), f"/api/stories/{story.uuid}/{path}").status_code
            != 404
        ]
        self.assertEqual(reachable, [])
        self.assertFalse(StoryView.objects.exists())
        self.assertFalse(StoryLike.objects.exists())

    def test_viewers_and_counts_stay_with_the_owner(self):
        story = self.create_story()
        self.as_user(self.jonas)
        self.client.post(f"/api/stories/{story.uuid}/view/")
        seen = self.client.get("/api/social/profiles/anna/").json()["stories"][0]
        self.assertIsNone(seen["like_count"])
        self.assertIsNone(seen["view_count"])
        self.assertEqual(self.client.get(f"/api/stories/{story.uuid}/viewers/").status_code, 404)

    def test_stories_of_suspended_or_inactive_authors_disappear(self):
        story = self.create_story()
        self.as_user(self.jonas)
        warning = Warning.objects.create(user=self.anna, reason=Reason.INSULT)
        Suspension.start(self.anna, warning, 0, timezone.now())
        self.assertEqual(self.client.get(f"/api/stories/{story.uuid}/image/").status_code, 404)

        Suspension.objects.all().delete()
        self.anna.is_active = False
        self.anna.save()
        self.assertEqual(self.client.get(f"/api/stories/{story.uuid}/image/").status_code, 404)


class RepostSecurityTests(SecurityTestCase):
    def assert_cannot_repost(self, post):
        self.assertEqual(self.client.post(f"/api/posts/{post.uuid}/repost/").status_code, 404)
        self.assertFalse(Repost.objects.exists())

    def test_cannot_repost_posts_outside_the_audience(self):
        self.assert_cannot_repost(
            Post.objects.create(author=self.eve, text="geheim", visibility="friends")
        )

    def test_cannot_repost_blocked_posts(self):
        self.assert_cannot_repost(
            Post.objects.create(author=self.eve, text="gesperrt", hidden_at=timezone.now())
        )

    def test_reposting_twice_keeps_one_repost(self):
        post = Post.objects.create(author=self.eve, text="Hallo")
        for _ in range(3):
            self.client.post(f"/api/posts/{post.uuid}/repost/")
        self.assertEqual(Repost.objects.count(), 1)

    def test_reposter_name_never_leaks_strangers(self):
        post = Post.objects.create(author=self.eve, text="Hallo")
        Repost.objects.create(user=self.jonas, post=post)
        data = self.client.get(f"/api/posts/{post.uuid}/").json()
        self.assertIsNone(data["reposter"])


class GlobalVisibilityTests(SecurityTestCase):
    def test_only_admins_can_reach_everyone(self):
        response = self.client.post("/api/posts/", {"text": "an alle", "visibility": "global"})
        self.assertEqual(response.status_code, 400)
        post = self.create_post()
        response = self.client.put(
            f"/api/posts/{post.uuid}/audience/",
            {"visibility": "global"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        post.refresh_from_db()
        self.assertEqual(post.visibility, "public")
