import shutil
import tempfile
from itertools import product

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from accounts.models import UserProfile
from accounts.roles import Role, set_role
from posts.models import ContactGroup

from .models import Follow, Friendship

User = get_user_model()
MEDIA = tempfile.mkdtemp()

AUDIENCES = ["followers", "friends", "groups"]
RELATIONS = ["stranger", "follower", "friend", "member", "admin", "self"]


def sees_private(audience, relation):
    return (
        relation in ("self", "admin")
        or {
            "followers": relation == "follower",
            "friends": relation == "friend",
            "groups": relation == "member",
        }[audience]
    )


@override_settings(MEDIA_ROOT=MEDIA)
class PictureMatrixTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.owner = User.objects.create(username="owner")
        self.group = ContactGroup.objects.create(owner=self.owner, name="Familie")
        self.profile = UserProfile.objects.create(user=self.owner)
        self.profile.public_picture.save("public.webp", ContentFile(b"public"))
        self.profile.private_picture.save("private.webp", ContentFile(b"private"), save=False)
        self.private_name = self.profile.private_picture.name
        self.profile.private_picture = ""
        self.profile.save()

    def viewer(self, relation):
        if relation == "self":
            return self.owner
        user = User.objects.create(username=f"{relation}-viewer")
        if relation == "follower":
            Follow.objects.create(follower=user, following=self.owner)
        if relation == "friend":
            Friendship.objects.create(user=user, friend=self.owner)
        if relation == "member":
            self.group.members.add(user)
        if relation == "admin":
            set_role(user, Role.ADMIN)
        return user

    def test_every_combination(self):
        for audience, relation in product(AUDIENCES, RELATIONS):
            with self.subTest(audience=audience, relation=relation):
                self.profile.private_picture = self.private_name
                self.profile.private_picture_visibility = audience
                self.profile.save()
                self.profile.private_picture_groups.set([self.group])

                self.client.force_login(self.viewer(relation))
                picture = self.client.get("/api/social/profiles/owner/").json()["picture"]
                private = self.client.get("/api/social/profiles/owner/pictures/private/")

                expected = sees_private(audience, relation)
                self.assertIn("/private/" if expected else "/public/", picture)
                self.assertEqual(private.status_code != 404, expected)
                User.objects.exclude(pk=self.owner.pk).delete()

    def test_without_private_picture_everyone_sees_the_public_one(self):
        for relation in RELATIONS:
            with self.subTest(relation=relation):
                self.client.force_login(self.viewer(relation))
                picture = self.client.get("/api/social/profiles/owner/").json()["picture"]
                self.assertIn("/public/", picture)
                User.objects.exclude(pk=self.owner.pk).delete()
