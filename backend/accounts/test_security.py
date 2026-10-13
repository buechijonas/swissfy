import hashlib
import hmac
import time
from io import StringIO
from unittest import mock
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase, override_settings

from .models import UserProfile
from .roles import Role, role_of, set_role
from .tests import SECRET, govex_user, signed_post

User = get_user_model()

GOVEX = {
    "GOVEX_CLIENT_SECRET": SECRET,
    "GOVEX_CLIENT_ID": "swissfy",
    "GOVEX_PUBLIC_URL": "https://govex.example",
    "GOVEX_REDIRECT_URI": "http://testserver/api/auth/oidc/callback/",
    "FRONTEND_URL": "http://frontend",
}


@override_settings(**GOVEX)
class LoginFlowTests(TestCase):
    def start_login(self, client=None):
        response = (client or self.client).get("/api/auth/oidc/login/")
        return response, (client or self.client).session.get("govex_oauth_state")

    def callback(self, userinfo, state, client=None, extra=""):
        with mock.patch("accounts.oidc.fetch_userinfo", return_value=userinfo):
            return (client or self.client).get(
                f"/api/auth/oidc/callback/?code=abc&state={state}{extra}"
            )

    def test_login_uses_pkce_and_random_state(self):
        response, state = self.start_login()
        query = parse_qs(urlparse(response["Location"]).query)
        self.assertTrue(response["Location"].startswith("https://govex.example/"))
        self.assertEqual(query["code_challenge_method"], ["S256"])
        self.assertEqual(query["state"], [state])
        self.assertGreaterEqual(len(state), 32)
        self.assertNotIn("code_verifier", query)
        _, other = self.start_login()
        self.assertNotEqual(state, other)

    def test_callback_without_started_login_is_rejected(self):
        response = self.callback({"sub": "s1"}, state="anything")
        self.assertEqual(response["Location"], "http://frontend/login?error=oidc_failed")
        self.assertFalse(User.objects.exists())

    def test_state_from_another_browser_is_rejected(self):
        victim, attacker = Client(), Client()
        _, attacker_state = self.start_login(attacker)
        self.start_login(victim)
        response = self.callback({"sub": "attacker"}, attacker_state, client=victim)
        self.assertEqual(response["Location"], "http://frontend/login?error=oidc_failed")
        self.assertNotIn("_auth_user_id", victim.session)

    def test_state_can_only_be_used_once(self):
        _, state = self.start_login()
        self.client.logout()
        self.start_login()
        self.client.logout()
        response = self.callback({"sub": "s1", "preferred_username": "x"}, state)
        self.assertEqual(response["Location"], "http://frontend/login?error=oidc_failed")

    def test_empty_state_is_rejected(self):
        self.start_login()
        with mock.patch("accounts.oidc.fetch_userinfo") as fetch:
            response = self.client.get("/api/auth/oidc/callback/?code=abc&state=")
        fetch.assert_not_called()
        self.assertEqual(response["Location"], "http://frontend/login?error=oidc_failed")

    def test_failed_token_exchange_logs_nobody_in(self):
        _, state = self.start_login()
        response = self.callback(None, state)
        self.assertEqual(response["Location"], "http://frontend/login?error=oidc_failed")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_rotates_the_session(self):
        _, state = self.start_login()
        before = self.client.session.session_key
        self.callback({"sub": "s1", "preferred_username": "jonas"}, state)
        self.assertNotEqual(self.client.session.session_key, before)

    def test_callback_never_redirects_off_site(self):
        for extra in [
            "&next=https://evil.example",
            "&redirect_uri=https://evil.example",
            "&return_to=//evil.example",
        ]:
            with self.subTest(extra=extra):
                _, state = self.start_login()
                response = self.callback(
                    {"sub": "s1", "preferred_username": "jonas"}, state, extra=extra
                )
                self.assertEqual(response["Location"], "http://frontend/")

    def test_govex_error_parameter_is_not_reflected(self):
        self.start_login()
        response = self.client.get("/api/auth/oidc/callback/?error=<script>alert(1)</script>")
        self.assertEqual(response["Location"], "http://frontend/login?error=oidc_failed")

    def test_account_redirect_only_goes_to_govex(self):
        with override_settings(GOVEX_ACCOUNT_URL="https://govex.example/account"):
            response = self.client.get("/api/auth/oidc/account/?next=https://evil.example")
        self.assertEqual(response["Location"], "https://govex.example/account")

    def test_never_links_existing_account_by_email(self):
        admin = User.objects.create(username="root", email="admin@swissfy.ch", is_superuser=True)
        _, state = self.start_login()
        self.callback(
            {"sub": "attacker", "preferred_username": "x", "email": "admin@swissfy.ch"}, state
        )
        new = User.objects.get(profile__govex_sub="attacker")
        self.assertNotEqual(new.pk, admin.pk)
        self.assertFalse(new.is_superuser)

    def test_userinfo_cannot_grant_roles_or_staff(self):
        _, state = self.start_login()
        self.callback(
            {
                "sub": "s1",
                "preferred_username": "jonas",
                "is_superuser": True,
                "is_staff": True,
                "groups": ["Admin"],
                "role": "admin",
            },
            state,
        )
        user = User.objects.get(username="jonas")
        self.assertFalse(user.is_superuser or user.is_staff)
        self.assertEqual(role_of(user), Role.DEFAULT)

    def test_meta_is_sanitised(self):
        _, state = self.start_login()
        self.callback(
            {
                "sub": "s1",
                "preferred_username": "jonas",
                "meta": {
                    "first_name": "x" * 1000,
                    "birthdate": "'; DROP TABLE auth_user;--",
                    "avatar": "../../../etc/passwd",
                },
            },
            state,
        )
        user = User.objects.get(username="jonas")
        self.assertEqual(len(user.first_name), 150)
        self.assertIsNone(user.profile.birthdate)
        self.assertEqual(user.profile.avatar, "")


@override_settings(**GOVEX)
class AdminTakeoverTests(TestCase):
    def setUp(self):
        call_command("bootstrap_admin", stdout=StringIO())
        self.admin = User.objects.get(username="admin")

    def login_as_govex(self, username, sub="attacker-sub"):
        self.client.get("/api/auth/oidc/login/")
        state = self.client.session["govex_oauth_state"]
        userinfo = {"sub": sub, "preferred_username": username}
        with mock.patch("accounts.oidc.fetch_userinfo", return_value=userinfo):
            self.client.get(f"/api/auth/oidc/callback/?code=abc&state={state}")
        return User.objects.get(profile__govex_sub=sub)

    def test_govex_user_cannot_take_the_admin_username(self):
        attacker = self.login_as_govex("admin")
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.username, "admin")
        self.assertNotEqual(attacker.username, "admin")
        self.assertTrue(attacker.username.startswith("govex-"))

    def test_bootstrap_admin_after_attack_keeps_attacker_unprivileged(self):
        attacker = self.login_as_govex("admin")
        call_command("bootstrap_admin", stdout=StringIO(), stderr=StringIO())
        attacker.refresh_from_db()
        self.assertFalse(attacker.is_superuser or attacker.is_staff)
        self.assertEqual(role_of(attacker), Role.DEFAULT)

    def test_bootstrap_admin_never_promotes_a_govex_identity(self):
        self.admin.delete()
        attacker = govex_user("admin", "attacker-sub")
        stderr = StringIO()
        call_command("bootstrap_admin", stdout=StringIO(), stderr=stderr)
        attacker.refresh_from_db()
        self.assertFalse(attacker.is_superuser or attacker.is_staff)
        self.assertIn("govex", stderr.getvalue())

    def test_rename_in_govex_cannot_take_the_admin_username(self):
        attacker = govex_user("eve", "attacker-sub")
        signed_post(
            self.client,
            "/api/auth/oidc/account-updated/",
            {"sub": "attacker-sub", "username": "admin", "email": "x@example.com"},
        )
        attacker.refresh_from_db()
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.username, "admin")
        self.assertNotEqual(attacker.username, "admin")
        self.assertFalse(attacker.is_superuser)

    def test_staff_names_stay_protected_case_by_case(self):
        User.objects.create(username="support", is_staff=True)
        attacker = self.login_as_govex("support")
        self.assertNotEqual(attacker.username, "support")

    def test_normal_unlinked_names_still_go_to_govex(self):
        User.objects.create(username="jonas")
        user = self.login_as_govex("jonas")
        self.assertEqual(user.username, "jonas")


@override_settings(**GOVEX)
class WebhookTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create(username="admin", is_superuser=True, is_staff=True)
        UserProfile.objects.create(user=self.admin)
        self.jonas = govex_user("jonas", "s1")

    def deleted(self, payload, **kwargs):
        return signed_post(self.client, "/api/auth/oidc/account-deleted/", payload, **kwargs)

    def updated(self, payload, **kwargs):
        return signed_post(self.client, "/api/auth/oidc/account-updated/", payload, **kwargs)

    def assert_untouched(self):
        self.assertTrue(User.objects.filter(pk=self.admin.pk, username="admin").exists())
        self.assertTrue(User.objects.filter(pk=self.jonas.pk, username="jonas").exists())

    def test_missing_or_odd_sub_deletes_nobody(self):
        for sub in [None, "", [], {}, 0, False, ["s1"], {"$ne": None}]:
            with self.subTest(sub=sub):
                self.assertEqual(self.deleted({"sub": sub}).status_code, 204)
                self.assert_untouched()
        self.assertEqual(self.deleted({}).status_code, 204)
        self.assert_untouched()

    def test_missing_sub_updates_nobody(self):
        self.updated({"sub": None, "username": "hacked"})
        self.assert_untouched()

    def test_forged_signatures_are_rejected(self):
        for secret in ["wrong", "", SECRET.upper(), SECRET + " "]:
            with self.subTest(secret=secret):
                self.assertEqual(self.deleted({"sub": "s1"}, secret=secret).status_code, 403)
        self.assert_untouched()

    def test_expired_and_future_timestamps_are_rejected(self):
        now = int(time.time())
        for timestamp in [now - 301, now + 301, 1, 10**12]:
            with self.subTest(timestamp=timestamp):
                response = self.deleted({"sub": "s1"}, timestamp=timestamp)
                self.assertEqual(response.status_code, 403)
        self.assert_untouched()

    def test_signature_is_bound_to_the_body(self):
        body = b'{"sub": "s1"}'
        timestamp = str(int(time.time()))
        response = self.client.post(
            "/api/auth/oidc/account-deleted/",
            body,
            content_type="application/json",
            headers={"X-Govex-Timestamp": timestamp, "X-Govex-Signature": "0" * 64},
        )
        self.assertEqual(response.status_code, 403)
        self.assert_untouched()

    def test_missing_headers_are_rejected(self):
        for headers in [
            {},
            {"X-Govex-Timestamp": str(int(time.time()))},
            {"X-Govex-Signature": "a"},
        ]:
            with self.subTest(headers=headers):
                response = self.client.post(
                    "/api/auth/oidc/account-deleted/",
                    b'{"sub": "s1"}',
                    content_type="application/json",
                    headers=headers,
                )
                self.assertEqual(response.status_code, 403)
        self.assert_untouched()

    def test_non_numeric_timestamps_are_rejected(self):
        for timestamp in ["-1", "1e9", " 1", "abc", "١٢٣"]:
            with self.subTest(timestamp=timestamp):
                response = self.client.post(
                    "/api/auth/oidc/account-deleted/",
                    b'{"sub": "s1"}',
                    content_type="application/json",
                    headers={"X-Govex-Timestamp": timestamp, "X-Govex-Signature": "a"},
                )
                self.assertEqual(response.status_code, 403)

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get("/api/auth/oidc/account-deleted/").status_code, 405)

    def test_without_configured_secret_nothing_is_accepted(self):
        with override_settings(GOVEX_CLIENT_SECRET=None):
            response = self.deleted({"sub": "s1"})
        self.assertEqual(response.status_code, 403)
        self.assert_untouched()

    def test_malformed_body_is_a_client_error(self):
        timestamp = str(int(time.time()))
        body = b"{not json"
        signature = hmac.new(
            SECRET.encode(), f"{timestamp}.".encode() + body, hashlib.sha256
        ).hexdigest()
        response = self.client.post(
            "/api/auth/oidc/account-deleted/",
            body,
            content_type="application/json",
            headers={"X-Govex-Timestamp": timestamp, "X-Govex-Signature": signature},
        )
        self.assertEqual(response.status_code, 400)


class AccountEndpointTests(TestCase):
    def setUp(self):
        self.anna = User.objects.create(username="anna", email="anna@example.com")
        self.anna.set_password("secret-password")
        self.anna.save()
        self.client.force_login(self.anna)

    def test_me_exposes_no_secrets(self):
        user = self.client.get("/api/auth/me/").json()["user"]
        for field in ["password", "is_superuser", "is_staff", "govex_sub", "last_login"]:
            self.assertNotIn(field, user)
        self.assertNotIn("pbkdf2", str(user))

    def test_consent_endpoint_only_accepts_known_fields(self):
        for field in ["is_superuser", "user", "id", "user_id", "__class__", "save", "pk"]:
            with self.subTest(field=field):
                response = self.client.post(f"/api/auth/consent/{field}/")
                self.assertEqual(response.status_code, 404)
        self.anna.refresh_from_db()
        self.assertFalse(self.anna.is_superuser)

    def test_logout_invalidates_the_session(self):
        session = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        self.client.post("/api/auth/logout/")
        other = Client()
        other.cookies[settings.SESSION_COOKIE_NAME] = session
        self.assertIsNone(other.get("/api/auth/me/").json()["user"])

    def test_link_govex_user_refuses_a_taken_identity(self):
        govex_user("jonas", "s1")
        with self.assertRaisesMessage(Exception, "already linked"):
            call_command("link_govex_user", "anna", "s1", stdout=StringIO())
        self.assertIsNone(UserProfile.objects.filter(user=self.anna).first())


class RoleTests(TestCase):
    def test_roles_do_not_grant_django_admin(self):
        user = User.objects.create(username="anna")
        for role in Role:
            with self.subTest(role=role):
                set_role(user, role)
                user.refresh_from_db()
                self.assertFalse(user.is_staff or user.is_superuser)
