from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.roles import Role, role_of, set_role
from posts.models import Comment, Post

from .models import Reason, Report, Warning

User = get_user_model()


class ModerationAccessTests(TestCase):
    def setUp(self):
        self.anna = User.objects.create(username="anna")
        self.eve = User.objects.create(username="eve")
        self.mod = User.objects.create(username="mod")
        self.admin = User.objects.create(username="boss")
        set_role(self.mod, Role.MODERATOR)
        set_role(self.admin, Role.ADMIN)
        self.post = Post.objects.create(author=self.anna, text="Hallo")
        self.comment = Comment.objects.create(post=self.post, author=self.anna, text="Hi")
        self.admin_post = Post.objects.create(author=self.admin, text="Admin")
        for target in [{"post": self.post}, {"comment": self.comment}, {"post": self.admin_post}]:
            Report.objects.create(reporter=self.eve, **target)

    def as_user(self, user):
        self.client.force_login(user)

    def moderation_urls(self):
        return [
            ("get", "/api/moderation/reports/", {}),
            ("get", f"/api/moderation/posts/{self.post.uuid}/", {}),
            ("get", f"/api/moderation/posts/{self.post.uuid}/comments/", {}),
            ("get", f"/api/moderation/comments/{self.comment.uuid}/", {}),
            ("get", f"/api/moderation/comments/{self.comment.uuid}/replies/", {}),
            ("post", f"/api/moderation/posts/{self.post.uuid}/warnings/", {"reason": "insult"}),
            ("post", f"/api/moderation/posts/{self.post.uuid}/dismiss/", {}),
            (
                "post",
                f"/api/moderation/comments/{self.comment.uuid}/warnings/",
                {"reason": "insult"},
            ),
            ("post", f"/api/moderation/comments/{self.comment.uuid}/dismiss/", {}),
        ]

    def test_non_moderators_cannot_moderate(self):
        for role in [Role.DEFAULT, Role.VERIFIED, Role.SUPPORT]:
            set_role(self.eve, role)
            self.as_user(self.eve)
            for method, url, data in self.moderation_urls():
                with self.subTest(role=role, url=url):
                    response = getattr(self.client, method)(
                        url, data, content_type="application/json"
                    )
                    self.assertEqual(response.status_code, 403)
        self.assertFalse(Warning.objects.exists())
        self.assertFalse(Report.objects.filter(resolved_at__isnull=False).exists())

    def test_moderators_cannot_act_on_admin_content(self):
        self.as_user(self.mod)
        for url in [
            f"/api/moderation/posts/{self.admin_post.uuid}/warnings/",
            f"/api/moderation/posts/{self.admin_post.uuid}/dismiss/",
        ]:
            with self.subTest(url=url):
                response = self.client.post(
                    url, {"reason": "insult"}, content_type="application/json"
                )
                self.assertEqual(response.status_code, 403)
        self.assertFalse(Warning.objects.filter(user=self.admin).exists())
        queue = self.client.get("/api/moderation/reports/").content.decode()
        self.assertNotIn(str(self.admin_post.uuid), queue)

    def test_moderators_cannot_report_admins(self):
        self.as_user(self.mod)
        response = self.client.post(f"/api/posts/{self.admin_post.uuid}/report/")
        self.assertEqual(response.status_code, 403)

    def test_warning_reason_must_be_known(self):
        self.as_user(self.mod)
        for reason in ["", "spam'--", None, ["insult"], {"$ne": ""}, "x" * 100]:
            with self.subTest(reason=reason):
                response = self.client.post(
                    f"/api/moderation/posts/{self.post.uuid}/warnings/",
                    {"reason": reason},
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 400)
        self.assertFalse(Warning.objects.exists())

    def test_unreported_content_cannot_be_warned(self):
        clean = Post.objects.create(author=self.anna, text="clean")
        self.as_user(self.mod)
        response = self.client.post(
            f"/api/moderation/posts/{clean.uuid}/warnings/",
            {"reason": Reason.INSULT},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_warnings_are_private(self):
        Warning.objects.create(user=self.anna, reason=Reason.INSULT, post=self.post)
        self.as_user(self.eve)
        self.assertEqual(self.client.get("/api/social/profiles/anna/status/").status_code, 403)
        self.as_user(self.anna)
        self.assertIsNone(self.client.get("/api/social/profiles/anna/status/").json()["reports"])
        self.as_user(self.mod)
        self.assertIsNotNone(self.client.get("/api/social/profiles/anna/status/").json()["reports"])


class AdministrationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create(username="boss")
        self.mod = User.objects.create(username="mod")
        self.anna = User.objects.create(username="anna")
        set_role(self.admin, Role.ADMIN)
        set_role(self.mod, Role.MODERATOR)

    def patch(self, username, data):
        return self.client.patch(
            f"/api/administration/users/{username}/", data, content_type="application/json"
        )

    def test_moderators_cannot_grant_roles(self):
        self.client.force_login(self.mod)
        for target, role in [("mod", "admin"), ("anna", "moderator"), ("boss", "default")]:
            with self.subTest(target=target, role=role):
                self.assertEqual(self.patch(target, {"role": role}).status_code, 403)
        self.assertEqual(role_of(self.mod), Role.MODERATOR)
        self.assertEqual(role_of(self.admin), Role.ADMIN)

    def test_admins_cannot_change_their_own_role(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.patch("boss", {"role": "default"}).status_code, 403)

    def test_role_must_be_known(self):
        self.client.force_login(self.admin)
        for role in ["superuser", "Admin", "root", "", None, ["admin"], {"$ne": ""}]:
            with self.subTest(role=role):
                self.assertEqual(self.patch("anna", {"role": role}).status_code, 400)
        self.assertEqual(role_of(self.anna), Role.DEFAULT)

    def test_other_fields_cannot_be_changed(self):
        self.client.force_login(self.admin)
        self.patch(
            "anna",
            {
                "role": "verified",
                "username": "hijacked",
                "first_name": "X",
                "is_superuser": True,
                "is_staff": True,
                "password": "x",
            },
        )
        self.anna.refresh_from_db()
        self.assertEqual(self.anna.username, "anna")
        self.assertEqual(self.anna.first_name, "")
        self.assertFalse(self.anna.is_superuser or self.anna.is_staff)
        self.assertEqual(role_of(self.anna), Role.VERIFIED)

    def test_only_patch_is_allowed(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.delete("/api/administration/users/anna/").status_code, 405)
        self.assertEqual(
            self.client.put(
                "/api/administration/users/anna/",
                {"role": "admin"},
                content_type="application/json",
            ).status_code,
            405,
        )
        self.assertTrue(User.objects.filter(username="anna").exists())
