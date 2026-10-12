from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from accounts.models import UserProfile
from accounts.roles import Role, set_role
from posts.hashtags import tag
from posts.models import Comment, Hashtag, Like, Post
from social.models import Follow

User = get_user_model()


class AchievementTests(TestCase):
    def setUp(self):
        self.anna = User.objects.create(username="anna")
        self.jonas = User.objects.create(username="jonas")

    def achievements(self, username="anna"):
        response = self.client.get(f"/api/social/profiles/{username}/achievements/")
        return {achievement["key"]: achievement for achievement in response.json()}

    def unlocked(self, username="anna"):
        return {key for key, tier in self.achievements(username).items() if tier["unlocked"]}

    def test_each_tier_doubles_the_requirement(self):
        self.client.force_login(self.anna)
        tiers = [tier for tier in self.achievements().values() if tier["group"] == "likes_given"]
        self.assertEqual([tier["target"] for tier in tiers], [10, 20, 40, 80, 160])
        self.assertEqual([tier["previous"] for tier in tiers], [0, 10, 20, 40, 80])
        self.assertEqual(tiers[1]["title"], "Button-Masher")

    def test_counts_activity_and_describes_next_level(self):
        post = Post.objects.create(author=self.anna, text="Hallo")
        Post.objects.create(author=self.anna, text="Versteckt", hidden_at=post.created_at)
        Like.objects.create(user=self.jonas, post=post)
        Like.objects.create(user=self.anna, post=post)
        self.client.force_login(self.anna)

        achievements = self.achievements()
        self.assertTrue(achievements["posts-1"]["unlocked"])
        self.assertFalse(achievements["posts-2"]["unlocked"])
        self.assertEqual(achievements["posts-2"]["count"], 1)
        self.assertEqual(achievements["posts-2"]["description"], "Veröffentliche 2 Posts.")
        self.assertEqual(achievements["likes_received-1"]["count"], 1)
        self.assertEqual(achievements["likes_given-1"]["count"], 1)

    def test_debate_needs_replies_from_both_sides(self):
        post = Post.objects.create(author=self.anna, text="Fondue oder Raclette?")
        start = Comment.objects.create(post=post, author=self.anna, text="Fondue")
        reply = Comment.objects.create(post=post, author=self.jonas, parent=start, text="Raclette")
        Comment.objects.filter(pk=reply.pk).update(created_at=timezone.now() - timedelta(days=9))
        self.client.force_login(self.anna)
        self.assertEqual(self.achievements()["long_debate-1"]["count"], 0)

        for _ in range(3):
            Comment.objects.create(post=post, author=self.anna, parent=reply, text="Fondue!")
        achievements = self.achievements()
        self.assertEqual(achievements["long_debate-1"]["count"], 9)
        self.assertTrue(achievements["long_debate-1"]["unlocked"])
        self.assertFalse(achievements["long_debate-2"]["unlocked"])
        self.assertTrue(achievements["sparring-1"]["unlocked"])

    def test_tiers_unlock_separately(self):
        self.client.force_login(self.anna)
        for index in range(10):
            follower = User.objects.create(username=f"fan{index}")
            Follow.objects.create(follower=follower, following=self.jonas)
        unlocked = self.unlocked("jonas")
        self.assertIn("followers-1", unlocked)
        self.assertIn("followers-2", unlocked)
        self.assertNotIn("followers-3", unlocked)
        self.assertEqual(self.achievements("jonas")["followers-2"]["title"], "Lokale Berühmtheit")

    def test_counts_likes_per_person(self):
        posts = [Post.objects.create(author=self.anna, text=str(i)) for i in range(5)]
        for post in posts:
            Like.objects.create(user=self.jonas, post=post)
        self.client.force_login(self.anna)
        self.assertIn("fanclub-1", self.unlocked())
        self.assertIn("superfan-1", self.unlocked("jonas"))

    def test_one_time_achievements(self):
        User.objects.filter(pk=self.jonas.pk).update(first_name="Jonas", last_name="Meier")
        UserProfile.objects.create(user=self.jonas, avatar="owl", birthdate="1990-01-01")
        self.client.force_login(self.jonas)
        achievements = self.achievements("jonas")
        self.assertTrue(achievements["og-1"]["unlocked"])
        self.assertTrue(achievements["og-1"]["bonus"])
        self.assertFalse(achievements["pioneer-1"]["bonus"])
        self.assertTrue(achievements["open_book-1"]["unlocked"])
        self.assertIsNone(achievements["og-1"]["target"])
        self.assertFalse(self.achievements()["open_book-1"]["unlocked"])

    def test_theme_posts_and_follows(self):
        for text in ("Neues Level #gaming #zocken", "Abend mit #nintendo", "Fondue #food"):
            tag(Post.objects.create(author=self.anna, text=text))
        Hashtag.objects.get(name="zocken").followers.add(self.anna)
        self.client.force_login(self.anna)

        achievements = self.achievements()
        self.assertEqual(achievements["topic_gaming_posts-2"]["title"], "Respawn-Profi")
        self.assertTrue(achievements["topic_gaming_posts-2"]["unlocked"])
        self.assertFalse(achievements["topic_gaming_posts-3"]["unlocked"])
        self.assertTrue(achievements["topic_food_posts-1"]["unlocked"])
        self.assertTrue(achievements["topic_gaming_follows-1"]["unlocked"])
        self.assertFalse(achievements["topic_horror_posts-1"]["unlocked"])

    def test_private_profile_hides_achievements(self):
        UserProfile.objects.create(user=self.anna, profile_visibility="followers")
        self.client.force_login(self.jonas)
        response = self.client.get("/api/social/profiles/anna/achievements/")
        self.assertEqual(response.status_code, 403)
        Follow.objects.create(follower=self.jonas, following=self.anna)
        self.assertEqual(self.achievements()["followers-1"]["count"], 1)

    def test_unlocks_are_backdated_and_kept(self):
        follows = []
        for index in range(5):
            follower = User.objects.create(username=f"fan{index}")
            follows.append(Follow.objects.create(follower=follower, following=self.anna))
        fifth = timezone.now() - timedelta(days=3)
        Follow.objects.filter(pk=follows[-1].pk).update(created_at=fifth)
        Follow.objects.filter(pk__in=[f.pk for f in follows[:-1]]).update(
            created_at=fifth - timedelta(days=1)
        )
        User.objects.filter(pk=self.anna.pk).update(date_joined=fifth - timedelta(days=10))
        self.client.force_login(self.anna)

        tier = self.achievements()["followers-1"]
        self.assertTrue(tier["unlocked"])
        self.assertEqual(tier["unlocked_at"][:10], fifth.date().isoformat())

        Follow.objects.filter(following=self.anna).delete()
        tier = self.achievements()["followers-1"]
        self.assertTrue(tier["unlocked"])
        self.assertEqual(tier["count"], 0)

    def test_easter_eggs_stay_secret_until_found(self):
        self.client.force_login(self.anna)
        egg = self.achievements()["egg_ill_be_back-1"]
        self.assertFalse(egg["unlocked"])
        self.assertIsNone(egg["title"])
        self.assertIsNone(egg["description"])

        post = Post.objects.create(author=self.jonas, text="Bis morgen")
        Comment.objects.create(post=post, author=self.anna, text="ILL BE BACK!!")
        Post.objects.create(author=self.anna, text="Hey Jonas, how you doin'?")
        Post.objects.create(author=self.anna, text="still be backup")
        achievements = self.achievements()
        self.assertEqual(achievements["egg_ill_be_back-1"]["title"], "I'll Be Back")
        self.assertTrue(achievements["egg_how_you_doin-1"]["unlocked"])
        self.assertFalse(achievements["egg_bazinga-1"]["unlocked"])

    def test_admin_sees_hidden_easter_eggs(self):
        set_role(self.jonas, Role.ADMIN)
        self.client.force_login(self.jonas)
        egg = self.achievements()["egg_gregor_samsa-1"]
        self.assertFalse(egg["unlocked"])
        self.assertEqual(egg["title"], "Verwandlung")
        self.assertIn("Kafka", egg["description"])
