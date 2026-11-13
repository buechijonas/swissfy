import json
import os
import subprocess
import sys
from uuid import uuid4

from django.conf import settings
from django.contrib.admindocs.views import extract_views_from_urlpatterns
from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import Client, TestCase
from django.urls import get_resolver

from swissfy.accounts.roles import Role, set_role
from swissfy.posts.models import Comment, Post

User = get_user_model()

PUBLIC = {
    "health",
    "govex-login",
    "govex-callback",
    "govex-account",
    "govex-account-deleted",
    "govex-account-updated",
    "auth-me",
    "posts-global-feed",
    "post-media-image",
    "post-media-video",
    "post-media-thumbnail",
    "changelog-list",
    "changelog-detail",
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


def routes():
    for _, route, _, name in extract_views_from_urlpatterns(get_resolver().url_patterns):
        if not route.startswith("django-admin"):
            yield route, name


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
        open_endpoints = [
            (method, path)
            for path, name in self.api_routes()
            if name not in PUBLIC
            for method in ["get", *UNSAFE]
            if self.client.generic(method.upper(), path).status_code not in (401, 403, 405)
        ]
        self.assertEqual(open_endpoints, [])

    def test_public_endpoints_leak_nothing_to_anonymous_users(self):
        self.assertEqual(self.client.get("/api/auth/me/").json(), {"user": None})
        self.assertEqual(self.client.get("/api/health/").json(), {"status": "ok"})

    def unsigned_post(self, path):
        return self.client.post(path, {"sub": "x"}, content_type="application/json")

    def test_signed_endpoints_reject_unsigned_requests(self):
        accepted = [
            path
            for path, name in self.api_routes()
            if name in SIGNED and self.unsigned_post(path).status_code != 403
        ]
        self.assertEqual(accepted, [])
        self.assertTrue(User.objects.filter(username="anna").exists())

    def test_inactive_users_are_locked_out(self):
        self.anna.is_active = False
        self.anna.save()
        self.client.force_login(self.anna)
        self.assertEqual(self.client.get("/api/posts/").status_code, 403)

    def assert_admin_endpoints_forbidden(self, role):
        set_role(self.anna, role)
        self.client.force_login(self.anna)
        self.assertEqual(self.client.get("/api/administration/roles/").status_code, 403)
        self.assertEqual(self.client.get("/api/administration/users/").status_code, 403)
        response = self.client.patch(
            "/api/administration/users/jonas/",
            {"role": "admin"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_default_users_cannot_use_admin_endpoints(self):
        self.assert_admin_endpoints_forbidden(Role.DEFAULT)

    def test_verified_users_cannot_use_admin_endpoints(self):
        self.assert_admin_endpoints_forbidden(Role.VERIFIED)

    def test_support_cannot_use_admin_endpoints(self):
        self.assert_admin_endpoints_forbidden(Role.SUPPORT)

    def test_moderators_cannot_use_admin_endpoints(self):
        self.assert_admin_endpoints_forbidden(Role.MODERATOR)

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

    def json_request(self, method, path):
        return self.client.generic(method.upper(), path, "{}", content_type="application/json")

    def test_every_unsafe_request_needs_a_csrf_token(self):
        unprotected = [
            (method, path)
            for path, name in self.api_routes()
            if name not in SIGNED
            for method in UNSAFE
            if self.json_request(method, path).status_code not in (403, 405)
        ]
        self.assertEqual(unprotected, [])

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

    def is_safe(self, response):
        return response.status_code < 500 and b"Traceback" not in response.content
        self.assertNotIn(b"syntax error", response.content)
        self.assertNotIn(b"psycopg", response.content)

    def test_query_parameters_are_never_interpreted(self):
        users = User.objects.count()
        unsafe = [
            (path, param, payload)
            for path, name in self.api_routes()
            if name not in PUBLIC
            for param in QUERY_PARAMS
            for payload in INJECTIONS
            if not self.is_safe(self.request(path, {param: payload}))
        ]
        self.assertEqual(unsafe, [])
        self.assertEqual(User.objects.count(), users)

    def path_with(self, route, payload):
        path = route.replace("<str:username>", payload).replace("<str:name>", payload)
        return "/" + path.replace("<str:field>", payload)

    def test_path_parameters_are_never_interpreted(self):
        templates = [route for route, _ in routes() if "<str:" in route]
        payloads = [
            payload
            for payload in INJECTIONS
            if "/" not in payload and "\x00" not in payload and "%" not in payload
        ]
        unsafe = [
            (route, payload)
            for route in templates
            for payload in payloads
            if not self.is_safe(self.request(self.path_with(route, payload)))
        ]
        self.assertEqual(unsafe, [])
        self.assertTrue(User.objects.filter(username="jonas").exists())

    def assert_search_finds_nothing(self, payload):
        response = self.client.get("/api/social/profiles/", {"q": payload * 2})
        self.assertEqual(response.json()["results"], [])

    def test_search_ignores_percent_wildcard(self):
        self.assert_search_finds_nothing("%")

    def test_search_ignores_underscore_wildcard(self):
        self.assert_search_finds_nothing("_")

    def test_search_ignores_double_percent_wildcard(self):
        self.assert_search_finds_nothing("%%")

    def test_search_ignores_sql_or_clause(self):
        self.assert_search_finds_nothing("' OR '1'='1")

    def post_comment(self, text):
        return self.client.post(
            f"/api/posts/{self.post.uuid}/comments/",
            {"text": text},
            content_type="application/json",
        )

    def stored_text(self, text):
        response = self.post_comment(text)
        return response.json()["text"] if response.status_code == 201 else None

    def test_json_bodies_with_injections_are_stored_verbatim(self):
        payloads = [payload[:500] for payload in INJECTIONS if "\x00" not in payload]
        altered = [payload for payload in payloads if self.stored_text(payload) != payload]
        self.assertEqual(altered, [])

    def test_null_bytes_in_bodies_are_rejected(self):
        response = self.client.post(
            f"/api/posts/{self.post.uuid}/comments/",
            {"text": "a\x00b"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_object_as_text_is_rejected(self):
        self.assertEqual(self.post_comment({"$gt": ""}).status_code, 400)

    def test_list_as_text_is_rejected(self):
        self.assertEqual(self.post_comment(["a"]).status_code, 400)

    def test_null_as_text_is_rejected(self):
        self.assertEqual(self.post_comment(None).status_code, 400)

    def test_boolean_as_text_is_rejected(self):
        self.assertEqual(self.post_comment(True).status_code, 400)


class MalformedRequestTests(Fixtures):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.anna)

    def put_raw(self, body, content_type="application/json"):
        return self.client.put("/api/chats/protection/", body, content_type=content_type)

    def test_unclosed_object_is_a_client_error(self):
        self.assertEqual(self.put_raw("{").status_code, 400)

    def test_unclosed_array_is_a_client_error(self):
        self.assertEqual(self.put_raw("[").status_code, 400)

    def test_missing_value_is_a_client_error(self):
        self.assertEqual(self.put_raw('{"mode": }').status_code, 400)

    def test_invalid_utf8_is_a_client_error(self):
        self.assertEqual(self.put_raw("\xff\xfe").status_code, 400)

    def test_json_null_is_a_client_error(self):
        self.assertEqual(self.put_raw("null").status_code, 400)

    def test_json_number_is_a_client_error(self):
        self.assertEqual(self.put_raw("1").status_code, 400)

    def test_json_string_is_a_client_error(self):
        self.assertEqual(self.put_raw('"x"').status_code, 400)

    def test_json_array_is_a_client_error(self):
        self.assertEqual(self.put_raw("[]").status_code, 400)

    def test_deeply_nested_json_is_a_client_error(self):
        self.assertEqual(self.put_raw("[" * 100_000 + "]" * 100_000).status_code, 400)

    def test_oversized_json_is_rejected(self):
        body = json.dumps({"mode": "standard", "padding": "a" * (3 * 1024 * 1024)})
        self.assertIn(self.put_raw(body).status_code, (400, 413))

    def put_with_content_type(self, content_type):
        return self.put_raw("<mode>standard</mode>", content_type=content_type)

    def test_xml_is_rejected(self):
        self.assertEqual(self.put_with_content_type("application/xml").status_code, 415)

    def test_yaml_is_rejected(self):
        self.assertEqual(self.put_with_content_type("text/yaml").status_code, 415)

    def test_pickle_is_rejected(self):
        response = self.put_with_content_type("application/x-python-pickle")
        self.assertEqual(response.status_code, 415)

    def get_health_from(self, host):
        return self.client.get("/api/health/", headers={"Host": host})

    def test_foreign_host_is_rejected(self):
        self.assertEqual(self.get_health_from("evil.example").status_code, 400)

    def test_foreign_subdomain_of_localhost_is_rejected(self):
        self.assertEqual(self.get_health_from("localhost.evil.example").status_code, 400)

    def test_host_with_credentials_trick_is_rejected(self):
        self.assertEqual(self.get_health_from("localhost:8000@evil.example").status_code, 400)

    def test_trace_is_rejected(self):
        self.assertIn(self.client.generic("TRACE", "/api/posts/").status_code, (403, 405))

    def test_propfind_is_rejected(self):
        self.assertIn(self.client.generic("PROPFIND", "/api/posts/").status_code, (403, 405))

    def test_connect_is_rejected(self):
        self.assertIn(self.client.generic("CONNECT", "/api/posts/").status_code, (403, 405))

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
    "CONTENT_ENCRYPTION_KEYS": "1:c3dpc3NmeS1sb2NhbC1jb250ZW50LWtleS1vbmx5ISE=",
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

    def refuses_to_start_without(self, missing):
        result = self.load_settings(**{missing: None})
        return result.returncode != 0 and "ImproperlyConfigured" in result.stderr

    def test_production_refuses_to_start_without_secrets(self):
        secrets = [key for key in PRODUCTION_ENV if key != "DJANGO_DEBUG"]
        optional = [key for key in secrets if not self.refuses_to_start_without(key)]
        self.assertEqual(optional, [])

    def test_production_never_falls_back_to_the_dev_chat_key(self):
        result = self.load_settings(CHAT_ENCRYPTION_KEY=None)
        self.assertNotEqual(result.returncode, 0)

    def assert_debug_off(self, value):
        result = self.load_settings(DJANGO_DEBUG=value)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["debug"])

    def test_debug_is_off_for_false(self):
        self.assert_debug_off("false")

    def test_debug_is_off_for_capitalized_false(self):
        self.assert_debug_off("False")

    def test_debug_is_off_for_zero(self):
        self.assert_debug_off("0")

    def test_debug_is_off_for_no(self):
        self.assert_debug_off("no")

    def test_debug_is_off_for_empty_value(self):
        self.assert_debug_off("")
