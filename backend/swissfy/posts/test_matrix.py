from itertools import product

from django.contrib.auth import get_user_model
from django.test import TestCase

from swissfy.accounts.models import UserProfile
from swissfy.accounts.roles import Role, set_role
from swissfy.social.models import Follow, Friendship

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


def expected_status(profile, audience, relation):
    return 200 if can_see(profile, audience, relation) else 404


class PostVisibilityMatrixTests(AudienceMatrix):
    def post_status(self, profile, audience, relation):
        self.set_profile(profile)
        post = Post.objects.create(author=self.author, text="Hallo", visibility=audience)
        if audience == "groups":
            post.groups.add(self.group)
        self.client.force_login(self.viewer(relation))
        status = self.client.get(f"/api/posts/{post.uuid}/").status_code
        User.objects.exclude(pk=self.author.pk).delete()
        return status

    def test_every_combination(self):
        wrong = [
            (profile, audience, relation)
            for profile, audience, relation in product(PROFILES, AUDIENCES, RELATIONS)
            if self.post_status(profile, audience, relation)
            != expected_status(profile, audience, relation)
        ]
        self.assertEqual(wrong, [])

    def test_global_posts_ignore_profile_and_relation(self):
        hidden = [
            (profile, relation)
            for profile, relation in product(PROFILES, RELATIONS)
            if self.post_status(profile, "global", relation) != 200
        ]
        self.assertEqual(hidden, [])


class StoryVisibilityMatrixTests(AudienceMatrix):
    def stories_seen_by(self, viewer):
        self.client.force_login(viewer)
        return self.client.get("/api/social/profiles/author/").json()["stories"]

    def sees_story(self, profile, audience, relation):
        self.set_profile(profile)
        Story.objects.all().delete()
        story = Story.objects.create(author=self.author, image="s.webp", visibility=audience)
        if audience == "groups":
            story.groups.add(self.group)
        seen = self.stories_seen_by(self.viewer(relation))
        User.objects.exclude(pk=self.author.pk).delete()
        return len(seen) == 1

    def test_every_combination(self):
        wrong = [
            (profile, audience, relation)
            for profile, audience, relation in product(PROFILES, AUDIENCES, RELATIONS)
            if self.sees_story(profile, audience, relation) != can_see(profile, audience, relation)
        ]
        self.assertEqual(wrong, [])

    def test_global_stories_stored_directly_are_hidden_from_strangers(self):
        Story.objects.create(author=self.author, image="s.webp", visibility="global")
        self.assertEqual(self.stories_seen_by(self.viewer("stranger")), [])

    def test_global_stories_stored_directly_are_hidden_from_followers(self):
        Story.objects.create(author=self.author, image="s.webp", visibility="global")
        self.assertEqual(self.stories_seen_by(self.viewer("follower")), [])


class RepostMatrixTests(AudienceMatrix):
    def repost_in_feed(self, profile, audience, relation):
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
        User.objects.exclude(pk=self.author.pk).delete()
        Post.objects.all().delete()
        return str(post.uuid) in [item["id"] for item in feed]

    def test_repost_reaches_followers_only_within_the_audience(self):
        wrong = [
            (profile, audience, relation)
            for profile, audience, relation in product(PROFILES, AUDIENCES, RELATIONS[:4])
            if self.repost_in_feed(profile, audience, relation)
            != can_see(profile, audience, relation)
        ]
        self.assertEqual(wrong, [])
