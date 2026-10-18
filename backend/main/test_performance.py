from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from accounts.models import UserProfile
from notifications.models import Notification
from posts.models import Comment, Like, Post, Repost, Story, StoryView
from social.models import Follow

User = get_user_model()


class QueryScalingTests(TestCase):
    def setUp(self):
        self.viewer = User.objects.create(username="viewer")
        self.client.force_login(self.viewer)
        self.created = 0

    def add_authors(self, count):
        for _ in range(count):
            self.created += 1
            author = User.objects.create(username=f"author{self.created}")
            UserProfile.objects.create(user=author, public_picture="profiles/p.webp")
            Follow.objects.create(follower=self.viewer, following=author)
            Follow.objects.create(follower=author, following=self.viewer)
            post = Post.objects.create(author=author, text=f"Feed #{self.created}")
            Like.objects.create(user=self.viewer, post=post)
            Comment.objects.create(post=post, author=author, text="Kommentar")
            Repost.objects.create(user=author, post=post)
            story = Story.objects.create(author=author, image="s.webp")
            StoryView.objects.create(user=self.viewer, story=story)
            Notification.objects.create(
                recipient=self.viewer, kind=Notification.Kind.FOLLOW, actor=author
            )

    def queries(self, url):
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200, url)
        return len(context)

    def assert_constant(self, url, setup=None):
        self.add_authors(3)
        small = self.queries(url)
        self.add_authors(15)
        large = self.queries(url)
        self.assertEqual(small, large, f"{url} grows from {small} to {large} queries")

    def test_feed(self):
        self.assert_constant("/api/posts/")

    def test_profile_search(self):
        self.assert_constant("/api/social/profiles/")

    def test_followers(self):
        self.assert_constant("/api/social/profiles/viewer/followers/")

    def test_notifications(self):
        self.assert_constant("/api/notifications/")

    def test_profile_with_stories(self):
        self.add_authors(1)
        small = self.queries("/api/social/profiles/author1/")
        for _ in range(10):
            Story.objects.create(author=User.objects.get(username="author1"), image="s.webp")
        large = self.queries("/api/social/profiles/author1/")
        self.assertLessEqual(large - small, 0, f"profile grows from {small} to {large} queries")


class LargeDataTests(TestCase):
    def test_feed_pages_stay_bounded_with_many_posts(self):
        viewer = User.objects.create(username="viewer")
        author = User.objects.create(username="author")
        Follow.objects.create(follower=viewer, following=author)
        Post.objects.bulk_create(Post(author=author, text=str(i)) for i in range(2000))
        self.client.force_login(viewer)

        seen = set()
        url = "/api/posts/"
        for _ in range(5):
            page = self.client.get(url).json()
            ids = [item["id"] for item in page["results"]]
            self.assertEqual(len(ids), 25)
            self.assertFalse(seen & set(ids))
            seen.update(ids)
            url = page["next"]

    def test_search_with_many_users_returns_one_page(self):
        User.objects.bulk_create(User(username=f"user{i:04}") for i in range(1500))
        viewer = User.objects.create(username="viewer")
        self.client.force_login(viewer)
        data = self.client.get("/api/social/profiles/", {"q": "user1"}).json()
        self.assertEqual(len(data["results"]), 20)
        self.assertIsNotNone(data["next"])
