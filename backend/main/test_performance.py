from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from swissfy.accounts.models import UserProfile
from swissfy.accounts.roles import Role, set_role
from swissfy.chats.models import ChatRequest, Message
from swissfy.moderation.models import Reason, Suspension, Warning
from swissfy.notifications.models import Notification
from swissfy.posts.models import Comment, Like, Post, Repost, Story, StoryView
from swissfy.social.models import Follow, FollowRequest

User = get_user_model()

PROFILE_QUERY_LIMIT = 12


class QueryScalingTests(TestCase):
    def setUp(self):
        self.viewer = User.objects.create(username="viewer")
        self.client.force_login(self.viewer)
        self.created = 0

    def add_authors(self, count):
        for _ in range(count):
            self.created += 1
            author = User.objects.create(username=f"author{self.created}")
            UserProfile.objects.update_or_create(
                user=author, defaults={"public_picture": "profiles/p.webp"}
            )
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
            FollowRequest.objects.create(follower=author, following=self.viewer)
            Notification.objects.create(
                recipient=self.viewer, kind=Notification.Kind.FOLLOW_REQUEST, actor=author
            )
            ChatRequest.objects.create(
                sender=author, recipient=self.viewer, status=ChatRequest.Status.ACCEPTED
            )
            Message.objects.create(
                sender=author, recipient=self.viewer, ciphertext="YQ==", iv="YQ=="
            )
            warning = Warning.objects.create(user=author, reason=Reason.SPAM)
            later = timezone.now() + timedelta(days=1)
            Suspension.objects.create(
                user=author, warning=warning, step=0, starts_at=later, ends_at=later
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

    def test_chat_conversations(self):
        self.assert_constant("/api/chats/conversations/")

    def test_admin_users(self):
        set_role(self.viewer, Role.ADMIN)
        self.assert_constant("/api/administration/users/")

    def test_moderation_status(self):
        set_role(self.viewer, Role.MODERATOR)
        self.add_authors(1)
        small = self.queries("/api/social/profiles/author1/status/")
        author = User.objects.get(username="author1")
        for _ in range(10):
            Warning.objects.create(user=author, reason=Reason.SPAM)
        large = self.queries("/api/social/profiles/author1/status/")
        self.assertEqual(small, large, f"status grows from {small} to {large} queries")

    def test_profile_counts_in_one_query(self):
        self.add_authors(15)
        self.assertLessEqual(self.queries("/api/social/profiles/author1/"), PROFILE_QUERY_LIMIT)

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
        users = User.objects.bulk_create(User(username=f"user{i:04}") for i in range(1500))
        UserProfile.objects.bulk_create(UserProfile(user=user) for user in users)
        viewer = User.objects.create(username="viewer")
        self.client.force_login(viewer)
        data = self.client.get("/api/social/profiles/", {"q": "user1"}).json()
        self.assertEqual(len(data["results"]), 20)
        self.assertIsNotNone(data["next"])
