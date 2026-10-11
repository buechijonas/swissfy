from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from accounts.models import UserProfile, get_or_create_profile
from accounts.roles import Role, role_of, set_role
from posts.models import Comment, Post

from .models import Report, Suspension, Warning
from .sanctions import role_locked_until, suspend, suspend_if_needed

User = get_user_model()


class ModerationTests(TestCase):
    def setUp(self):
        self.anna = User.objects.create(username="anna")
        self.jonas = User.objects.create(username="jonas")
        self.eve = User.objects.create(username="eve")
        self.mod = User.objects.create(username="mod")
        set_role(self.mod, Role.MODERATOR)
        self.post = Post.objects.create(author=self.anna, text="Hallo")
        self.comment = Comment.objects.create(post=self.post, author=self.anna, text="Hi")

    def as_user(self, user):
        self.client.force_login(user)

    def report(self, kind, target):
        return self.client.post(f"/api/{kind}/{target.uuid}/report/")

    def queue(self, status="open"):
        return self.client.get("/api/moderation/reports/", {"status": status})

    def test_report_once_and_not_own(self):
        self.as_user(self.anna)
        self.assertEqual(self.report("posts", self.post).status_code, 403)

        self.as_user(self.jonas)
        self.assertEqual(self.report("posts", self.post).json(), {"reported": True})
        self.assertEqual(self.report("posts", self.post).status_code, 200)
        self.report("comments", self.comment)
        self.assertEqual(Report.objects.count(), 2)

        data = self.client.get(f"/api/posts/{self.post.uuid}/").json()
        self.assertEqual((data["reported"], data["can_report"]), (True, True))

    def test_queue_needs_moderator(self):
        self.as_user(self.jonas)
        self.assertEqual(self.queue().status_code, 403)
        self.as_user(self.mod)
        self.assertEqual(self.queue().status_code, 200)

    def test_queue_counts_reports(self):
        for user in (self.jonas, self.eve):
            self.as_user(user)
            self.report("posts", self.post)
        self.report("comments", self.comment)

        self.as_user(self.mod)
        results = self.queue().json()["results"]
        self.assertEqual(
            [(item["type"], item["report_count"]) for item in results],
            [("comment", 1), ("post", 2)],
        )
        self.assertFalse(results[0]["comment"]["can_vote"])
        self.assertEqual(results[0]["post"]["id"], str(self.post.uuid))

    def test_moderator_sees_hidden_reported_post(self):
        self.post.visibility = Post.Visibility.FRIENDS
        self.post.save()
        self.as_user(self.mod)
        self.assertEqual(
            self.client.get(f"/api/moderation/posts/{self.post.uuid}/").status_code, 404
        )

        Report.objects.create(reporter=self.jonas, post=self.post)
        data = self.client.get(f"/api/moderation/posts/{self.post.uuid}/").json()
        self.assertEqual(data["report_count"], 1)
        self.assertEqual(len(data["reasons"]), 40)
        comments = self.client.get(f"/api/moderation/posts/{self.post.uuid}/comments/").json()
        self.assertEqual(len(comments["results"]), 1)

    def test_warning_resolves_reports_and_shows_in_status(self):
        Report.objects.create(reporter=self.jonas, comment=self.comment)
        self.as_user(self.mod)
        url = f"/api/moderation/comments/{self.comment.uuid}/warnings/"
        self.assertEqual(self.client.post(url, {"reason": "nope"}).status_code, 400)
        response = self.client.post(url, {"reason": "spam"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.client.post(url, {"reason": "insult"}).status_code, 400)
        detail = self.client.get(f"/api/moderation/comments/{self.comment.uuid}/").json()
        self.assertFalse(detail["can_warn"])
        self.assertEqual(response.json()["warning"]["reason"], "Spam")
        self.assertEqual(self.queue().json()["results"], [])
        resolved = self.queue("resolved").json()["results"]
        self.assertEqual([(item["type"], item["warned"]) for item in resolved], [("comment", True)])
        self.assertEqual(Warning.objects.get().user, self.anna)

        status = self.client.get("/api/social/profiles/anna/status/").json()
        self.assertEqual(status["events"][0]["link"], f"/moderation/comments/{self.comment.uuid}")
        self.as_user(self.anna)
        warnings = self.client.get("/api/social/profiles/anna/status/").json()["events"]
        self.assertEqual((len(warnings), warnings[0]["link"]), (1, None))
        self.assertTrue(self.client.get("/api/social/profiles/anna/").json()["can_view_warnings"])
        self.as_user(self.jonas)
        self.assertEqual(self.client.get("/api/social/profiles/anna/status/").status_code, 403)
        self.assertFalse(self.client.get("/api/social/profiles/anna/").json()["can_view_warnings"])

    def test_warned_post_is_hidden_from_everyone_but_moderation(self):
        Report.objects.create(reporter=self.jonas, post=self.post)
        self.as_user(self.mod)
        self.client.post(f"/api/moderation/posts/{self.post.uuid}/warnings/", {"reason": "spam"})
        data = self.client.get(f"/api/moderation/posts/{self.post.uuid}/").json()
        self.assertTrue(data["post"]["hidden"])
        self.assertEqual(self.client.get(f"/api/posts/{self.post.uuid}/").status_code, 200)

        for user in (self.anna, self.jonas):
            self.as_user(user)
            self.assertEqual(self.client.get(f"/api/posts/{self.post.uuid}/").status_code, 404)
            self.assertEqual(self.client.get("/api/posts/users/anna/").json()["results"], [])

    def test_warned_comment_and_replies_are_hidden(self):
        reply = Comment.objects.create(
            post=self.post, parent=self.comment, author=self.jonas, text="Re"
        )
        Report.objects.create(reporter=self.jonas, comment=self.comment)
        self.as_user(self.mod)
        self.client.post(
            f"/api/moderation/comments/{self.comment.uuid}/warnings/", {"reason": "spam"}
        )
        replies = self.client.get(f"/api/moderation/comments/{self.comment.uuid}/replies/").json()
        self.assertEqual(len(replies["results"]), 1)

        for user in (self.anna, self.jonas):
            self.as_user(user)
            post = self.client.get(f"/api/posts/{self.post.uuid}/").json()
            comments = self.client.get(f"/api/posts/{self.post.uuid}/comments/").json()
            self.assertEqual((post["comment_count"], comments["results"]), (0, []))
            self.assertEqual(self.client.get(f"/api/comments/{reply.uuid}/").status_code, 404)

    def test_dismiss(self):
        Report.objects.create(reporter=self.jonas, post=self.post)
        self.as_user(self.mod)
        self.client.post(f"/api/moderation/posts/{self.post.uuid}/dismiss/")
        self.assertEqual(self.queue().json()["results"], [])
        resolved = self.queue("resolved").json()["results"]
        self.assertEqual([(item["type"], item["warned"]) for item in resolved], [("post", False)])
        self.assertFalse(Warning.objects.exists())

    def test_author_role_badge(self):
        self.as_user(self.jonas)
        comment = self.client.get(f"/api/posts/{self.post.uuid}/comments/").json()["results"][0]
        self.assertIsNone(comment["author"]["role"])
        set_role(self.anna, Role.VERIFIED)
        comment = self.client.get(f"/api/posts/{self.post.uuid}/comments/").json()["results"][0]
        self.assertEqual(comment["author"]["role"], {"key": "verified", "label": "Verifiziert"})


class AdministrationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create(username="boss")
        set_role(self.admin, Role.ADMIN)
        self.anna = User.objects.create(username="anna", first_name="Anna")
        self.mod = User.objects.create(username="mod")
        set_role(self.mod, Role.MODERATOR)

    def users(self, **params):
        data = self.client.get("/api/administration/users/", params).json()
        return [(user["username"], user["role"]) for user in data["results"]]

    def test_only_admin(self):
        self.client.force_login(self.mod)
        self.assertEqual(self.client.get("/api/administration/users/").status_code, 403)

    def test_list_filter_and_change_role(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.users(q="ann"), [("anna", "default")])
        self.assertEqual(self.users(role="moderator"), [("mod", "moderator")])
        self.assertEqual(self.users(role="default"), [("anna", "default")])

        response = self.client.patch(
            "/api/administration/users/anna/", {"role": "support"}, content_type="application/json"
        )
        self.assertEqual(response.json()["role"], "support")
        self.assertEqual(self.users(role="support"), [("anna", "support")])

        response = self.client.patch(
            "/api/administration/users/boss/", {"role": "default"}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(self.client.get("/api/administration/roles/").json()), 5)


class SanctionTests(TestCase):
    def setUp(self):
        self.anna = User.objects.create(username="anna")
        self.jonas = User.objects.create(username="jonas")
        self.mod = User.objects.create(username="mod")
        set_role(self.mod, Role.MODERATOR)

    def warn(self, days_ago=0):
        post = Post.objects.create(author=self.anna, text="x")
        Report.objects.create(reporter=self.jonas, post=post)
        self.client.force_login(self.mod)
        self.client.post(f"/api/moderation/posts/{post.uuid}/warnings/", {"reason": "spam"})
        if days_ago:
            Warning.objects.filter(post=post).update(
                created_at=timezone.now() - timedelta(days=days_ago)
            )

    def durations(self):
        return [
            (suspension.ends_at - suspension.starts_at).days if suspension.ends_at else None
            for suspension in Suspension.objects.order_by("id")
        ]

    def test_third_warning_suspends_for_three_days(self):
        self.warn()
        self.warn()
        self.assertFalse(Suspension.objects.exists())
        self.warn()
        self.assertEqual(self.durations(), [3])

    def test_escalation_queues_after_running_suspension(self):
        for _ in range(7):
            self.warn()
        self.assertEqual(self.durations(), [3, 7, 30, 365, None])
        first, second = Suspension.objects.order_by("id")[:2]
        self.assertEqual(second.starts_at, first.ends_at)
        self.warn()
        self.assertEqual(Suspension.objects.count(), 5)

    def test_expired_warnings_do_not_count(self):
        self.warn(days_ago=100)
        self.warn(days_ago=100)
        self.warn()
        self.assertFalse(Suspension.objects.exists())

        self.client.force_login(self.anna)
        events = self.client.get("/api/social/profiles/anna/status/").json()["events"]
        self.assertEqual([event["expired"] for event in events], [False, True, True])

    def test_suspended_user_is_blocked_and_hidden(self):
        post = Post.objects.create(author=self.jonas, text="offen")
        for _ in range(3):
            self.warn()

        self.client.force_login(self.anna)
        response = self.client.post("/api/posts/", {"text": "Hallo"})
        self.assertEqual(response.status_code, 403)
        self.assertIn("gesperrt", response.json()["detail"])
        self.assertEqual(
            self.client.post(f"/api/posts/{post.uuid}/comments/", {"text": "x"}).status_code, 403
        )
        self.assertEqual(self.client.post("/api/chats/jonas/request/").status_code, 403)
        events = self.client.get("/api/social/profiles/anna/status/").json()["events"]
        self.assertEqual(
            (events[0]["type"], events[0]["duration"], events[0]["state"]),
            ("suspension", "3 Tage", "active"),
        )

        self.client.force_login(self.jonas)
        self.assertEqual(self.client.get("/api/social/profiles/anna/").status_code, 404)
        users = self.client.get("/api/social/profiles/").json()["results"]
        self.assertNotIn("anna", [user["username"] for user in users])

        self.client.force_login(self.mod)
        self.assertEqual(self.client.get("/api/social/profiles/anna/").status_code, 200)

        Suspension.objects.update(ends_at=timezone.now() - timedelta(minutes=1))
        self.client.force_login(self.anna)
        self.assertEqual(self.client.post("/api/posts/", {"text": "Wieder da"}).status_code, 201)


class PrivilegedViewTests(TestCase):
    def setUp(self):
        self.anna = User.objects.create(username="anna", first_name="Anna")
        get_or_create_profile(self.anna)
        UserProfile.objects.filter(user=self.anna).update(profile_visibility="friends")
        self.jonas = User.objects.create(username="jonas")
        self.mod = User.objects.create(username="mod")
        set_role(self.mod, Role.MODERATOR)
        self.admin = User.objects.create(username="boss")
        set_role(self.admin, Role.ADMIN)
        self.post = Post.objects.create(author=self.anna, text="geheim", visibility="friends")
        self.hidden = Post.objects.create(author=self.anna, text="weg", hidden_at=timezone.now())
        Report.objects.create(reporter=self.jonas, post=self.post)

    def test_moderator_sees_warnings_and_reports_of_private_profile(self):
        self.client.force_login(self.mod)
        profile = self.client.get("/api/social/profiles/anna/").json()
        self.assertEqual((profile["can_view"], profile["can_view_warnings"]), (False, True))
        status = self.client.get("/api/social/profiles/anna/status/").json()
        self.assertEqual(
            [(item["type"], item["open_count"]) for item in status["reports"]], [("Post", 1)]
        )
        self.assertEqual(self.client.get(f"/api/posts/{self.post.uuid}/").status_code, 200)

    def test_owner_does_not_get_reports(self):
        self.client.force_login(self.anna)
        self.assertIsNone(self.client.get("/api/social/profiles/anna/status/").json()["reports"])

    def test_admin_sees_everything(self):
        self.client.force_login(self.admin)
        profile = self.client.get("/api/social/profiles/anna/").json()
        self.assertEqual((profile["can_view"], profile["first_name"]), (True, "Anna"))
        posts = self.client.get("/api/posts/users/anna/").json()["results"]
        self.assertEqual(
            {(post["text"], post["hidden"]) for post in posts}, {("geheim", False), ("weg", True)}
        )
        users = self.client.get("/api/social/profiles/", {"q": "Anna"}).json()["results"]
        self.assertEqual([user["username"] for user in users], ["anna"])


class PrivateBadgeTests(TestCase):
    def test_role_badge_hidden_for_locked_profiles(self):
        viewer = User.objects.create(username="viewer")
        secret = User.objects.create(username="secret")
        set_role(secret, Role.VERIFIED)
        UserProfile.objects.create(user=secret, profile_visibility="friends")
        post = Post.objects.create(author=viewer, text="offen")
        Comment.objects.create(post=post, author=secret, text="psst")

        self.client.force_login(viewer)
        comment = self.client.get(f"/api/posts/{post.uuid}/comments/").json()["results"][0]
        self.assertIsNone(comment["author"]["role"])
        users = self.client.get("/api/social/profiles/").json()["results"]
        self.assertNotIn("role", users[0])
        self.assertNotIn("role", self.client.get("/api/social/profiles/secret/").json())

        admin = User.objects.create(username="boss")
        set_role(admin, Role.ADMIN)
        self.client.force_login(admin)
        comment = self.client.get(f"/api/posts/{post.uuid}/comments/").json()["results"][0]
        self.assertEqual(comment["author"]["role"]["key"], "verified")


class RoleLockTests(TestCase):
    def setUp(self):
        self.anna = User.objects.create(username="anna")
        set_role(self.anna, Role.VERIFIED)
        self.admin = User.objects.create(username="boss")
        set_role(self.admin, Role.ADMIN)

    def warn(self, days_ago=0):
        warning = Warning.objects.create(user=self.anna, reason="spam")
        Warning.objects.filter(pk=warning.pk).update(
            created_at=timezone.now() - timedelta(days=days_ago)
        )
        return Warning.objects.get(pk=warning.pk)

    def change_role(self, role):
        self.client.force_login(self.admin)
        return self.client.patch(
            "/api/administration/users/anna/", {"role": role}, content_type="application/json"
        )

    def test_suspension_revokes_verification_and_locks_role(self):
        for _ in range(3):
            warning = self.warn()
        suspend_if_needed(warning)
        self.assertEqual(role_of(self.anna), Role.DEFAULT)
        self.assertEqual(self.change_role("verified").status_code, 403)
        users = self.client.get("/api/administration/users/", {"q": "anna"}).json()["results"]
        self.assertIsNotNone(users[0]["role_locked_until"])

    def test_role_unlocks_once_warnings_expired_and_suspension_over(self):
        warning = self.warn(days_ago=100)
        suspend(self.anna, warning, 0, timezone.now() - timedelta(days=100))
        self.assertEqual(self.change_role("verified").status_code, 200)

    def test_lifetime_suspension_locks_forever(self):
        warning = self.warn(days_ago=200)
        suspend(self.anna, warning, 4, timezone.now() - timedelta(days=200))
        self.assertEqual(role_locked_until(self.anna), "forever")


class ModeratorReportedContentTests(TestCase):
    def test_moderator_sees_only_reported_content_of_private_profile(self):
        anna = User.objects.create(username="anna")
        UserProfile.objects.create(user=anna, profile_visibility="friends")
        reporter = User.objects.create(username="jonas")
        mod = User.objects.create(username="mod")
        set_role(mod, Role.MODERATOR)
        reported = Post.objects.create(author=anna, text="gemeldet", thumbnail="x.webp")
        Post.objects.create(author=anna, text="privat")
        other = Post.objects.create(author=reporter, text="fremd", visibility="friends")
        comment = Comment.objects.create(post=other, author=anna, text="frech")
        Report.objects.create(reporter=reporter, post=reported)
        Report.objects.create(reporter=reporter, comment=comment)

        self.client.force_login(mod)
        tiles = self.client.get("/api/posts/users/anna/", {"images": 1}).json()["results"]
        self.assertEqual([post["text"] for post in tiles], ["gemeldet"])
        activities = self.client.get("/api/posts/users/anna/activities/").json()["results"]
        self.assertEqual(
            [(item["type"], item["text"]) for item in activities],
            [("comment", "frech"), ("post", "gemeldet")],
        )

        public = Post.objects.create(author=reporter, text="offen")
        Comment.objects.create(post=public, author=anna, text="harmlos")
        activities = self.client.get("/api/posts/users/anna/activities/").json()["results"]
        self.assertNotIn("harmlos", [item["text"] for item in activities])

        self.client.force_login(reporter)
        self.assertEqual(self.client.get("/api/posts/users/anna/").json()["results"], [])
        self.assertEqual(self.client.get("/api/posts/users/anna/activities/").json()["results"], [])

    def test_suspension_directly_above_its_warning_in_timeline(self):
        anna = User.objects.create(username="anna")
        warnings = [Warning.objects.create(user=anna, reason="spam") for _ in range(3)]
        suspend_if_needed(warnings[-1])
        self.client.force_login(anna)
        events = self.client.get("/api/social/profiles/anna/status/").json()["events"]
        self.assertEqual(
            [(event["type"], event["id"]) for event in events[:2]],
            [("suspension", Suspension.objects.get().pk), ("warning", warnings[-1].pk)],
        )
