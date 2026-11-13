import shutil
import tempfile
from itertools import product

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from swissfy.accounts.roles import Role, set_role
from swissfy.posts.models import ContactGroup

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


def expected_access(audience, relation):
    if sees_private(audience, relation):
        return "private", True
    return "public", False


@override_settings(MEDIA_ROOT=MEDIA)
class PictureMatrixTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.owner = User.objects.create(username="owner")
        self.group = ContactGroup.objects.create(owner=self.owner, name="Familie")
        self.profile = self.owner.profile
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

    def shown_picture(self, relation):
        self.client.force_login(self.viewer(relation))
        picture = self.client.get("/api/social/profiles/owner/").json()["picture"] or ""
        private = self.client.get("/api/social/profiles/owner/pictures/private/")
        User.objects.exclude(pk=self.owner.pk).delete()
        kind = "private" if "/private/" in picture else "public" if "/public/" in picture else None
        return kind, private.status_code != 404

    def private_picture_access(self, audience, relation):
        self.profile.private_picture = self.private_name
        self.profile.private_picture_visibility = audience
        self.profile.save()
        self.profile.private_picture_groups.set([self.group])
        return self.shown_picture(relation)

    def test_every_combination(self):
        wrong = [
            (audience, relation)
            for audience, relation in product(AUDIENCES, RELATIONS)
            if self.private_picture_access(audience, relation)
            != expected_access(audience, relation)
        ]
        self.assertEqual(wrong, [])

    def test_without_private_picture_everyone_sees_the_public_one(self):
        wrong = [relation for relation in RELATIONS if self.shown_picture(relation)[0] != "public"]
        self.assertEqual(wrong, [])
