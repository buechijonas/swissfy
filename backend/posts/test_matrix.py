from itertools import product

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import UserProfile
from accounts.roles import Role, set_role
from social.models import Follow, Friendship

from .models import ContactGroup, Post, Repost, Story

User = get_user_model()

PROFILES = ["public", "followers", "friends"]
AUDIENCES = ["public", "followers", "friends", "groups"]
RELATIONS = ["stranger", "follower", "friend", "member", "admin", "self"]


def can_see(profile, audience, relation):
    if relation in ("self", "admin"):
        return True
    follows = relation == "follower"
    friend = relation == "friend"
    profile_ok = profile == "public" or (profile == "followers" and follows) or friend
    audience_ok = (
        audience == "public"
        or (audience == "followers" and follows)
        or (audience == "friends" and friend)
        or (audience == "groups" and relation == "member")
    )
    return profile_ok and audience_ok


class AudienceMatrix(TestCase):
    def setUp(self):
        self.author = User.objects.create(username="author")
        self.group = ContactGroup.objects.create(owner=self.author, name="Familie")

    def viewer(self, relation):
        if relation == "self":
            return self.author
        user = User.objects.create(username=f"{relation}-viewer")
        if relation == "follower":
            Follow.objects.create(follower=user, following=self.author)
        if relation == "friend":
            Friendship.objects.create(user=user, friend=self.author)
        if relation == "member":
            self.group.members.add(user)
        if relation == "admin":
            set_role(user, Role.ADMIN)
        return user

    def set_profile(self, visibility):
        UserProfile.objects.update_or_create(
            user=self.author, defaults={"profile_visibility": visibility}
        )


class PostVisibilityMatrixTests(AudienceMatrix):
    def check(self, profile, audience, relation, expected):
        self.set_profile(profile)
        post = Post.objects.create(author=self.author, text="Hallo", visibility=audience)
        if audience == "groups":
            post.groups.add(self.group)
        viewer = self.viewer(relation)
        self.client.force_login(viewer)
        status = self.client.get(f"/api/posts/{post.uuid}/").status_code
        self.assertEqual(status, 200 if expected else 404)

    def test_every_combination(self):
        for profile, audience, relation in product(PROFILES, AUDIENCES, RELATIONS):
            with self.subTest(profile=profile, audience=audience, relation=relation):
                self.check(profile, audience, relation, can_see(profile, audience, relation))
                User.objects.exclude(pk=self.author.pk).delete()

    def test_global_posts_ignore_profile_and_relation(self):
        for profile, relation in product(PROFILES, RELATIONS):
            with self.subTest(profile=profile, relation=relation):
                self.check(profile, "global", relation, True)
                User.objects.exclude(pk=self.author.pk).delete()


class StoryVisibilityMatrixTests(AudienceMatrix):
    def stories_seen_by(self, viewer):
        self.client.force_login(viewer)
        return self.client.get("/api/social/profiles/author/").json()["stories"]

    def test_every_combination(self):
        for profile, audience, relation in product(PROFILES, AUDIENCES, RELATIONS):
            with self.subTest(profile=profile, audience=audience, relation=relation):
                self.set_profile(profile)
                Story.objects.all().delete()
                story = Story.objects.create(
                    author=self.author, image="s.webp", visibility=audience
                )
                if audience == "groups":
                    story.groups.add(self.group)
                seen = self.stories_seen_by(self.viewer(relation))
                self.assertEqual(len(seen), 1 if can_see(profile, audience, relation) else 0)
                User.objects.exclude(pk=self.author.pk).delete()

    def test_global_stories_stored_directly_are_not_widened(self):
        Story.objects.create(author=self.author, image="s.webp", visibility="global")
        for relation in ("stranger", "follower"):
            with self.subTest(relation=relation):
                self.assertEqual(self.stories_seen_by(self.viewer(relation)), [])


class RepostMatrixTests(AudienceMatrix):
    def test_repost_reaches_followers_only_within_the_audience(self):
        for profile, audience, relation in product(PROFILES, AUDIENCES, RELATIONS[:4]):
            with self.subTest(profile=profile, audience=audience, relation=relation):
                self.set_profile(profile)
                post = Post.objects.create(author=self.author, text="Teilen", visibility=audience)
                if audience == "groups":
                    post.groups.add(self.group)
                reposter = User.objects.create(username="reposter")
                Repost.objects.create(user=reposter, post=post)
                viewer = self.viewer(relation)
                Follow.objects.create(follower=viewer, following=reposter)

                self.client.force_login(viewer)
                feed = self.client.get("/api/posts/").json()["results"]
                in_feed = str(post.uuid) in [item["id"] for item in feed]
                self.assertEqual(in_feed, can_see(profile, audience, relation))
                User.objects.exclude(pk=self.author.pk).delete()
                Post.objects.all().delete()
