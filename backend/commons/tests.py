import base64
import io
import os
import shutil
import tempfile
from pathlib import Path

from cryptography.exceptions import InvalidTag
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import TextField, Value
from django.db.models.functions import Cast
from django.test import TestCase, override_settings
from PIL import Image

from accounts.roles import Role, set_role
from posts.models import Comment, Post, PostImage
from social.models import Friendship

from .backfill import encrypt_rows
from .encryption import CHUNK, FILE_MAGIC

User = get_user_model()
MEDIA = tempfile.mkdtemp()


def raw(model, field, pk):
    return model.objects.values_list(Cast(field, TextField()), flat=True).get(pk=pk)


def write_raw(model, field, pk, value):
    model.objects.filter(pk=pk).update(**{field: Value(value, output_field=TextField())})


def webp():
    data = io.BytesIO()
    Image.new("RGB", (30, 20), "red").save(data, format="WEBP")
    return data.getvalue()


@override_settings(MEDIA_ROOT=MEDIA)
class EncryptionTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.anna = User.objects.create(username="anna")

    def test_text_is_stored_encrypted(self):
        post = Post.objects.create(author=self.anna, text="Hallo Welt")
        stored = raw(Post, "text", post.pk)
        self.assertTrue(stored.startswith("enc:1:"))
        self.assertNotIn("Hallo", stored)
        self.assertEqual(Post.objects.get().text, "Hallo Welt")

    def test_tampered_text_is_rejected(self):
        post = Post.objects.create(author=self.anna, text="Hallo")
        prefix, data = raw(Post, "text", post.pk).rsplit(":", 1)
        data = bytearray(base64.b64decode(data))
        data[-1] ^= 1
        write_raw(Post, "text", post.pk, f"{prefix}:{base64.b64encode(data).decode()}")
        with self.assertRaises(InvalidTag):
            Post.objects.get()

    def test_text_cannot_be_moved_to_another_field(self):
        post = Post.objects.create(author=self.anna, text="Hallo")
        comment = Comment.objects.create(post=post, author=self.anna, text="Antwort")
        write_raw(Comment, "text", comment.pk, raw(Post, "text", post.pk))
        with self.assertRaises(InvalidTag):
            Comment.objects.get()

    def test_files_are_stored_encrypted_and_seekable(self):
        data = os.urandom(3 * CHUNK + 5)
        name = default_storage.save("posts/clip.mp4", ContentFile(data))
        stored = Path(default_storage.path(name)).read_bytes()
        self.assertTrue(stored.startswith(FILE_MAGIC))
        self.assertNotIn(data[:64], stored)
        self.assertEqual(default_storage.size(name), len(data))
        with default_storage.open(name) as file:
            self.assertEqual(file.read(), data)
            file.seek(CHUNK - 3)
            self.assertEqual(file.read(10), data[CHUNK - 3 : CHUNK + 7])

    def test_truncated_file_is_rejected(self):
        name = default_storage.save("posts/clip.mp4", ContentFile(os.urandom(2 * CHUNK)))
        path = Path(default_storage.path(name))
        path.write_bytes(path.read_bytes()[: -(CHUNK + 16)])
        with default_storage.open(name) as file, self.assertRaises(InvalidTag):
            file.read()


@override_settings(MEDIA_ROOT=MEDIA)
class BackfillTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.anna = User.objects.create(username="anna")
        self.friend = User.objects.create(username="friend")
        self.stranger = User.objects.create(username="stranger")
        self.admin = User.objects.create(username="admin")
        set_role(self.admin, Role.ADMIN)
        Friendship.objects.create(user=self.anna, friend=self.friend)
        Friendship.objects.create(user=self.friend, friend=self.anna)
        self.image = webp()
        for visibility in [Post.Visibility.PUBLIC, Post.Visibility.FRIENDS]:
            post = Post.objects.create(author=self.anna, text=visibility, visibility=visibility)
            write_raw(Post, "text", post.pk, f"alt {visibility}")
            image = PostImage.objects.create(
                post=post, file=f"posts/{visibility}.webp", width=30, height=20, position=0
            )
            path = Path(default_storage.path(image.file.name))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(self.image)

    def seen_by(self, user):
        self.client.force_login(user)
        posts = self.client.get("/api/posts/users/anna/").json()["results"]
        return [
            (
                post["text"],
                [
                    b"".join(self.client.get(image["url"]).streaming_content)
                    for image in post["images"]
                ],
            )
            for post in posts
        ]

    def test_old_posts_keep_content_and_visibility(self):
        users = [self.anna, self.friend, self.stranger, self.admin]
        before = [self.seen_by(user) for user in users]
        self.assertEqual([len(posts) for posts in before], [2, 2, 1, 2])
        self.assertEqual(before[0][0][1], [self.image])

        encrypt_rows(Post, texts=["text"])
        encrypt_rows(PostImage, files=["file"])
        encrypt_rows(PostImage, files=["file"])

        self.assertEqual([self.seen_by(user) for user in users], before)
        for image in PostImage.objects.all():
            stored = Path(default_storage.path(image.file.name)).read_bytes()
            self.assertTrue(stored.startswith(FILE_MAGIC))
        for post in Post.objects.all():
            self.assertTrue(raw(Post, "text", post.pk).startswith("enc:1:"))
