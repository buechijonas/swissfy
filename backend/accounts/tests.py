import hashlib
import hmac
import json
import time
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from .models import UserConsent, UserProfile

User = get_user_model()

SECRET = "test-secret"


def signed_post(client, path, payload, secret=SECRET, timestamp=None):
    body = json.dumps(payload).encode()
    timestamp = str(timestamp or int(time.time()))
    signature = hmac.new(
        secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256
    ).hexdigest()
    return client.post(
        path,
        body,
        content_type="application/json",
        headers={"X-Govex-Timestamp": timestamp, "X-Govex-Signature": signature},
    )


def govex_user(username, sub):
    user = User.objects.create(username=username)
    UserProfile.objects.create(user=user, govex_sub=sub)
    return user


@override_settings(
    GOVEX_CLIENT_SECRET=SECRET,
    GOVEX_REDIRECT_URI="http://testserver/api/auth/oidc/callback/",
    FRONTEND_URL="http://frontend",
)
class GovexCallbackTests(TestCase):
    def start_login(self):
        self.client.get("/api/auth/oidc/login/")
        return self.client.session["govex_oauth_state"]

    def callback(self, userinfo, state=None):
        state = state or self.start_login()
        with mock.patch("accounts.oidc.fetch_userinfo", return_value=userinfo):
            return self.client.get(f"/api/auth/oidc/callback/?code=abc&state={state}")

    def test_rejects_wrong_state(self):
        self.start_login()
        response = self.callback({"sub": "s1"}, state="forged")
        self.assertEqual(response["Location"], "http://frontend/login?error=oidc_failed")
        self.assertFalse(User.objects.exists())

    def test_first_login_creates_user_with_default_role_and_meta(self):
        response = self.callback(
            {
                "sub": "s1",
                "preferred_username": "jonas",
                "email": "jonas@example.com",
                "meta": {"first_name": "Jonas", "birthdate": "2000-01-31", "avatar": "owl"},
            }
        )
        self.assertEqual(response["Location"], "http://frontend/")
        user = User.objects.get(username="jonas")
        self.assertEqual(user.profile.govex_sub, "s1")
        self.assertEqual(user.first_name, "Jonas")
        self.assertEqual(str(user.profile.birthdate), "2000-01-31")
        self.assertEqual(user.profile.avatar, "owl")
        self.assertEqual(list(user.groups.values_list("name", flat=True)), ["Standard"])
        self.assertFalse(user.has_usable_password())

    def test_never_links_existing_account_by_username(self):
        local = User.objects.create(username="admin")
        self.callback({"sub": "s1", "preferred_username": "admin"})
        local.refresh_from_db()
        self.assertEqual(local.username, f"admin-{local.pk}")
        self.assertEqual(User.objects.get(username="admin").profile.govex_sub, "s1")


@override_settings(GOVEX_CLIENT_SECRET=SECRET)
class GovexWebhookTests(TestCase):
    def test_rejects_bad_signature(self):
        user = govex_user("jonas", "s1")
        response = signed_post(
            self.client, "/api/auth/oidc/account-deleted/", {"sub": "s1"}, secret="wrong"
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(User.objects.filter(pk=user.pk).exists())

    def test_rejects_stale_timestamp(self):
        govex_user("jonas", "s1")
        response = signed_post(
            self.client,
            "/api/auth/oidc/account-deleted/",
            {"sub": "s1"},
            timestamp=int(time.time()) - 3600,
        )
        self.assertEqual(response.status_code, 403)

    def test_account_deleted_removes_user(self):
        user = govex_user("jonas", "s1")
        response = signed_post(self.client, "/api/auth/oidc/account-deleted/", {"sub": "s1"})
        self.assertEqual(response.status_code, 204)
        self.assertFalse(User.objects.filter(pk=user.pk).exists())

    def test_account_updated_syncs_user_and_meta(self):
        user = govex_user("jonas", "s1")
        response = signed_post(
            self.client,
            "/api/auth/oidc/account-updated/",
            {
                "sub": "s1",
                "username": "jonas2",
                "email": "new@example.com",
                "meta": {"last_name": "Büchi", "avatar": "not-an-avatar"},
            },
        )
        self.assertEqual(response.status_code, 204)
        user.refresh_from_db()
        self.assertEqual((user.username, user.email, user.last_name), ("jonas2", "new@example.com", "Büchi"))
        self.assertEqual(user.profile.avatar, "")


class ConsentTests(TestCase):
    def setUp(self):
        self.user = govex_user("jonas", "s1")
        self.client.force_login(self.user)

    def test_me_reports_open_consent(self):
        data = self.client.get("/api/auth/me/").json()
        self.assertEqual(
            data["user"]["consent"], {"privacy": False, "terms": False, "disclaimer": False}
        )

    def test_accept_consent(self):
        response = self.client.post("/api/auth/consent/terms/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserConsent.objects.get(user=self.user).terms)

    def test_unknown_consent_field(self):
        response = self.client.post("/api/auth/consent/cookies/")
        self.assertEqual(response.status_code, 404)
