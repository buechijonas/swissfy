import json
import os
import subprocess
import sys
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import Client, TestCase
from django.urls import URLResolver, get_resolver

from accounts.roles import Role, set_role
from posts.models import Comment, Post

User = get_user_model()

PUBLIC = {
    "health",
    "govex-login",
    "govex-callback",
    "govex-account",
    "govex-account-deleted",
    "govex-account-updated",
    "me",
    "global-feed",
    "post-image",
    "post-video",
    "post-thumbnail",
}
SIGNED = {"govex-account-deleted", "govex-account-updated"}
UNSAFE = ["post", "put", "patch", "delete"]

INJECTIONS = [
    "' OR '1'='1",
    "1; DROP TABLE auth_user;--",
    '" OR 1=1 --',
    "1' UNION SELECT username, password FROM auth_user--",
    "admin'--",
    "') OR ('a'='a",
    "1 AND SLEEP(5)",
    "'; SELECT pg_sleep(5);--",
    '{"$gt": ""}',
    "[$ne]=1",
    "../../../../etc/passwd",
    "..%2F..%2F..%2Fetc%2Fpasswd",
    "%00",
    "\x00",
    "a\x00b",
    "%s%s%s%n",
    "{0.__class__.__mro__}",
    "${7*7}",
    "{{7*7}}",
    "<script>alert(1)</script>",
    "\u202egnp.exe",
    "𝕒𝕕𝕞𝕚𝕟",
    "(a+)+$",
    "*",
    "%",
    "_",
    "\\",
    "-1",
    "0",
    "99999999999999999999999999",
    "1e309",
    "NaN",
    "true",
    "null",
    "a" * 5000,
]
QUERY_PARAMS = [
    "q",
    "page",
    "folder",
    "before",
    "after",
    "from",
    "status",
    "role",
    "images",
    "videos",
    "read",
    "cursor",
]


def routes(patterns=None, prefix=""):
    for pattern in get_resolver().url_patterns if patterns is None else patterns:
        if isinstance(pattern, URLResolver):
            if str(pattern.pattern).startswith("django-admin"):
                continue
            yield from routes(pattern.url_patterns, prefix + str(pattern.pattern))
        else:
            yield prefix + str(pattern.pattern), pattern.name


class Fixtures(TestCase):
    def setUp(self):
        self.anna = User.objects.create(username="anna")
        self.jonas = User.objects.create(username="jonas")
        self.post = Post.objects.create(author=self.jonas, text="Hallo")
        self.comment = Comment.objects.create(post=self.post, author=self.jonas, text="Hi")

    def fill(self, route):
        return "/" + route.replace("<uuid:uuid>", str(self.post.uuid)).replace(
            "<int:position>", "0"
        ).replace("<int:pk>", "1").replace("<str:username>", "jonas").replace(
            "<str:name>", "swiss"
        ).replace(
            "<str:field>", "terms"
        )

    def api_routes(self):
        return [(self.fill(route), name) for route, name in routes()]


class AuthenticationRequiredTests(Fixtures):
    def test_every_private_endpoint_rejects_anonymous_requests(self):
        for path, name in self.api_routes():
            if name in PUBLIC:
                continue
            for method in ["get", *UNSAFE]:
                with self.subTest(path=path, method=method):
                    response = getattr(self.client, method)(path)
                    self.assertIn(response.status_code, (401, 403, 405))

    def test_public_endpoints_leak_nothing_to_anonymous_users(self):
        self.assertEqual(self.client.get("/api/auth/me/").json(), {"user": None})
        self.assertEqual(self.client.get("/api/health/").json(), {"status": "ok"})

    def test_signed_endpoints_reject_unsigned_requests(self):
        for path, name in self.api_routes():
            if name not in SIGNED:
                continue
            with self.subTest(path=path):
                response = self.client.post(path, {"sub": "x"}, content_type="application/json")
                self.assertEqual(response.status_code, 403)
                self.assertTrue(User.objects.filter(username="anna").exists())

    def test_inactive_users_are_locked_out(self):
        self.anna.is_active = False
        self.anna.save()
        self.client.force_login(self.anna)
        self.assertEqual(self.client.get("/api/posts/").status_code, 403)

    def test_admin_endpoints_need_admin_role(self):
        for role in [Role.DEFAULT, Role.VERIFIED, Role.SUPPORT, Role.MODERATOR]:
            set_role(self.anna, role)
            self.client.force_login(self.anna)
            for path in [
                "/api/administration/roles/",
                "/api/administration/users/",
            ]:
                with self.subTest(role=role, path=path):
                    self.assertEqual(self.client.get(path).status_code, 403)
            response = self.client.patch(
                "/api/administration/users/jonas/",
                {"role": "admin"},
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 403)

    def test_django_admin_needs_staff(self):
        self.client.force_login(self.anna)
        response = self.client.get("/django-admin/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/django-admin/login/", response["Location"])


class CsrfTests(Fixtures):
    def setUp(self):
        super().setUp()
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.anna)

    def test_every_unsafe_request_needs_a_csrf_token(self):
        for path, name in self.api_routes():
            if name in SIGNED:
                continue
            for method in UNSAFE:
                with self.subTest(path=path, method=method):
                    response = getattr(self.client, method)(
                        path, {}, content_type="application/json"
                    )
                    self.assertIn(response.status_code, (403, 405))

    def test_forged_csrf_token_is_rejected(self):
        self.client.cookies[settings.CSRF_COOKIE_NAME] = "a" * 32
        response = self.client.post(
            f"/api/posts/{self.post.uuid}/like/", headers={"X-CSRFToken": "b" * 32}
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.post.likes.exists())

    def test_csrf_token_from_a_foreign_origin_is_rejected(self):
        self.client.get("/api/auth/me/")
        token = self.client.cookies[settings.CSRF_COOKIE_NAME].value
        response = self.client.post(
            f"/api/posts/{self.post.uuid}/like/",
            headers={"X-CSRFToken": token, "Origin": "https://evil.example"},
            secure=True,
        )
        self.assertEqual(response.status_code, 403)

    def test_valid_csrf_token_is_accepted(self):
        self.client.get("/api/auth/me/")
        token = self.client.cookies[settings.CSRF_COOKIE_NAME].value
        response = self.client.post(
            f"/api/posts/{self.post.uuid}/like/", headers={"X-CSRFToken": token}
        )
        self.assertEqual(response.status_code, 200)

    def test_logout_needs_post_with_csrf(self):
        self.assertEqual(self.client.get("/api/auth/logout/").status_code, 405)
        self.assertEqual(self.client.post("/api/auth/logout/").status_code, 403)
        self.assertEqual(self.client.get("/api/auth/me/").json()["user"]["username"], "anna")


class InjectionTests(Fixtures):
    def setUp(self):
        super().setUp()
        set_role(self.anna, Role.ADMIN)
        self.client.force_login(self.anna)

    def request(self, path, data=None):
        with transaction.atomic():
            return self.client.get(path, data)

    def assert_safe(self, response):
        self.assertLess(response.status_code, 500)
        self.assertNotIn(b"Traceback", response.content)
        self.assertNotIn(b"syntax error", response.content)
        self.assertNotIn(b"psycopg", response.content)

    def test_query_parameters_are_never_interpreted(self):
        users = User.objects.count()
        for path, name in self.api_routes():
            if name in PUBLIC:
                continue
            for param in QUERY_PARAMS:
                for payload in INJECTIONS:
                    with self.subTest(path=path, param=param, payload=payload[:40]):
                        self.assert_safe(self.request(path, {param: payload}))
        self.assertEqual(User.objects.count(), users)

    def test_path_parameters_are_never_interpreted(self):
        templates = [route for route, _ in routes() if "<str:" in route]
        for route in templates:
            for payload in INJECTIONS:
                if "/" in payload or "\x00" in payload or "%" in payload:
                    continue
                path = "/" + route.replace("<str:username>", payload).replace(
                    "<str:name>", payload
                ).replace("<str:field>", payload)
                with self.subTest(route=route, payload=payload[:40]):
                    self.assert_safe(self.request(path))
        self.assertTrue(User.objects.filter(username="jonas").exists())

    def test_search_does_not_match_sql_wildcards(self):
        for payload in ["%", "_", "%%", "' OR '1'='1"]:
            with self.subTest(payload=payload):
                response = self.client.get("/api/social/profiles/", {"q": payload * 2})
                self.assertEqual(response.json()["results"], [])

    def test_json_bodies_with_injections_are_stored_verbatim(self):
        for payload in INJECTIONS:
            if "\x00" in payload:
                continue
            with self.subTest(payload=payload[:40]):
                response = self.client.post(
                    f"/api/posts/{self.post.uuid}/comments/",
                    {"text": payload[:500]},
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 201)
                self.assertEqual(response.json()["text"], payload[:500])

    def test_null_bytes_in_bodies_are_rejected(self):
        response = self.client.post(
            f"/api/posts/{self.post.uuid}/comments/",
            {"text": "a\x00b"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_wrong_json_types_are_rejected(self):
        for value in [{"$gt": ""}, ["a"], None, True]:
            with self.subTest(value=value):
                response = self.client.post(
                    f"/api/posts/{self.post.uuid}/comments/",
                    {"text": value},
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 400)


class MalformedRequestTests(Fixtures):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.anna)

    def put_raw(self, body, content_type="application/json"):
        return self.client.put("/api/chats/protection/", body, content_type=content_type)

    def test_broken_json_is_a_client_error(self):
        for body in ["{", "[", '{"mode": }', "\xff\xfe", "null", "1", '"x"', "[]"]:
            with self.subTest(body=body):
                self.assertEqual(self.put_raw(body).status_code, 400)

    def test_deeply_nested_json_is_a_client_error(self):
        self.assertEqual(self.put_raw("[" * 100_000 + "]" * 100_000).status_code, 400)

    def test_oversized_json_is_rejected(self):
        body = json.dumps({"mode": "standard", "padding": "a" * (3 * 1024 * 1024)})
        self.assertIn(self.put_raw(body).status_code, (400, 413))

    def test_unsupported_content_types_are_rejected(self):
        for content_type in ["application/xml", "text/yaml", "application/x-python-pickle"]:
            with self.subTest(content_type=content_type):
                response = self.put_raw("<mode>standard</mode>", content_type=content_type)
                self.assertEqual(response.status_code, 415)

    def test_foreign_host_headers_are_rejected(self):
        for host in ["evil.example", "localhost.evil.example", "localhost:8000@evil.example"]:
            with self.subTest(host=host):
                response = self.client.get("/api/health/", headers={"Host": host})
                self.assertEqual(response.status_code, 400)

    def test_unknown_methods_are_rejected(self):
        for method in ["TRACE", "PROPFIND", "CONNECT"]:
            with self.subTest(method=method):
                response = self.client.generic(method, "/api/posts/")
                self.assertIn(response.status_code, (403, 405))

    def test_server_errors_do_not_leak_details(self):
        response = self.client.get(f"/api/posts/{uuid4()}/")
        self.assertEqual(response.status_code, 404)
        self.assertNotIn(b"Traceback", response.content)
        self.assertNotIn(b"DEBUG", response.content)


class ResponseHeaderTests(Fixtures):
    def test_api_responses_carry_security_headers(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response["Referrer-Policy"], "same-origin")
        self.assertEqual(response["Cross-Origin-Opener-Policy"], "same-origin")

    def test_no_cors_headers_for_foreign_origins(self):
        response = self.client.get("/api/auth/me/", headers={"Origin": "https://evil.example"})
        self.assertNotIn("Access-Control-Allow-Origin", response)
        self.assertNotIn("Access-Control-Allow-Credentials", response)

    def test_session_cookie_is_http_only(self):
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
        self.assertIn(settings.SESSION_COOKIE_SAMESITE, ("Lax", "Strict"))
        self.assertIn(settings.CSRF_COOKIE_SAMESITE, ("Lax", "Strict"))


PRODUCTION_ENV = {
    "DJANGO_DEBUG": "false",
    "DJANGO_SECRET_KEY": "x" * 50,
    "CHAT_ENCRYPTION_KEY": "c3dpc3NmeS1sb2NhbC1jaGF0LWtleS1kZXYtb25seSE=",
    "GOVEX_PUBLIC_URL": "https://auth.example",
    "GOVEX_ACCOUNT_URL": "https://auth.example/account",
    "GOVEX_CLIENT_ID": "swissfy",
    "GOVEX_CLIENT_SECRET": "secret",
    "GOVEX_REDIRECT_URI": "https://swissfy.example/api/auth/oidc/callback/",
    "CONSENT_PRIVATE_KEY": "consent-key",
}


class ProductionSettingsTests(TestCase):
    def load_settings(self, **overrides):
        env = {
            key: value
            for key, value in os.environ.items()
            if key not in PRODUCTION_ENV and not key.startswith("GOVEX_")
        }
        env.update({**PRODUCTION_ENV, **overrides})
        env = {key: value for key, value in env.items() if value is not None}
        code = (
            "import json, main.settings as s; print(json.dumps({"
            "'debug': s.DEBUG, 'session': s.SESSION_COOKIE_SECURE, "
            "'csrf': s.CSRF_COOKIE_SECURE, 'chat_key': s.CHAT_ENCRYPTION_KEY}))"
        )
        return subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            env=env,
            cwd=settings.BASE_DIR,
        )

    def test_production_settings_are_hardened(self):
        result = self.load_settings()
        self.assertEqual(result.returncode, 0, result.stderr)
        loaded = json.loads(result.stdout)
        self.assertEqual((loaded["debug"], loaded["session"], loaded["csrf"]), (False, True, True))

    def test_production_refuses_to_start_without_secrets(self):
        for missing in PRODUCTION_ENV:
            if missing == "DJANGO_DEBUG":
                continue
            with self.subTest(missing=missing):
                result = self.load_settings(**{missing: None})
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("ImproperlyConfigured", result.stderr)

    def test_production_never_falls_back_to_the_dev_chat_key(self):
        result = self.load_settings(CHAT_ENCRYPTION_KEY=None)
        self.assertNotEqual(result.returncode, 0)

    def test_debug_is_off_unless_explicitly_enabled(self):
        for value in ["false", "False", "0", "no", ""]:
            with self.subTest(value=value):
                result = self.load_settings(DJANGO_DEBUG=value)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse(json.loads(result.stdout)["debug"])
