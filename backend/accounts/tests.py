import base64
import hashlib
import hmac
import json
import time
from datetime import timedelta
from unittest import mock

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from .consent import attested_status, sign, status_of
from .models import DeviceToken, UserConsent, UserProfile

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

    def test_repeated_callback_after_login_goes_home(self):
        state = self.start_login()
        self.callback({"sub": "s1", "preferred_username": "jonas"}, state=state)
        response = self.callback({"sub": "s1", "preferred_username": "jonas"}, state=state)
        self.assertEqual(response["Location"], "http://frontend/")
        self.assertEqual(User.objects.count(), 1)

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
        self.assertEqual(
            (user.username, user.email, user.last_name), ("jonas2", "new@example.com", "Büchi")
        )
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
        with mock.patch("accounts.views.push_to_govex"):
            response = self.client.post("/api/auth/consent/terms/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserConsent.objects.get(user=self.user).terms)

    def test_unknown_consent_field(self):
        response = self.client.post("/api/auth/consent/cookies/")
        self.assertEqual(response.status_code, 404)


class DeviceTokenTests(TestCase):
    def setUp(self):
        self.user = govex_user("jonas", "s1")
        self.client.force_login(self.user)

    def issue(self, token=None):
        return self.client.post(
            "/api/auth/device/", {"token": token}, content_type="application/json"
        ).json()["token"]

    def restore(self, token):
        return self.client.post(
            "/api/auth/device/restore/", {"token": token}, content_type="application/json"
        )

    def test_issues_and_keeps_token(self):
        token = self.issue()
        self.assertEqual(self.issue(token), token)
        self.assertEqual(DeviceToken.objects.count(), 1)
        self.assertNotEqual(DeviceToken.objects.get().token_hash, token)

    def test_replaces_foreign_token(self):
        other = govex_user("anna", "s2")
        self.client.force_login(other)
        foreign = self.issue()
        self.client.force_login(self.user)
        self.assertNotEqual(self.issue(foreign), foreign)

    def test_restores_session_after_cookies_are_gone(self):
        token = self.issue()
        self.client.cookies.clear()
        response = self.restore(token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["username"], "jonas")
        self.assertEqual(self.client.get("/api/auth/me/").json()["user"]["username"], "jonas")

    def test_rejects_unknown_or_stale_token(self):
        token = self.issue()
        self.client.cookies.clear()
        self.assertEqual(self.restore("forged").status_code, 401)
        DeviceToken.objects.update(last_used_at=timezone.now() - timedelta(days=400))
        self.assertEqual(self.restore(token).status_code, 401)

    def test_forgetting_device_revokes_token(self):
        token = self.issue()
        self.assertEqual(self.client.delete("/api/auth/device/").status_code, 204)
        self.assertFalse(DeviceToken.objects.exists())
        self.client.cookies.clear()
        self.assertEqual(self.restore(token).status_code, 401)

    def test_logout_revokes_device(self):
        token = self.issue()
        self.client.post("/api/auth/logout/")
        self.assertFalse(DeviceToken.objects.exists())
        self.assertEqual(self.restore(token).status_code, 401)


class ConsentPushTests(TestCase):
    def setUp(self):
        self.user = govex_user("jonas", "s1")

    def test_accepting_consent_pushes_status_to_govex(self):
        self.client.force_login(self.user)
        with mock.patch("accounts.views.push_to_govex") as push:
            self.client.post("/api/auth/consent/terms/")
        push.assert_called_once_with("s1")

    def test_status_of_reports_own_consent(self):
        UserConsent.objects.create(user=self.user, privacy=True)
        self.assertEqual(
            status_of("s1"), {"consent": {"privacy": True, "terms": False, "disclaimer": False}}
        )

    def test_signed_status_names_swissfy_and_the_account(self):
        key = ec.generate_private_key(ec.SECP256R1())
        pem = key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode()
        with override_settings(CONSENT_PRIVATE_KEY=pem):
            token = sign({"iss": "swissfy", "sub": "s1", **status_of("s1")})
        header, body, signature = token.split(".")
        raw = base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4))
        der = encode_dss_signature(int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big"))
        key.public_key().verify(der, f"{header}.{body}".encode(), ec.ECDSA(hashes.SHA256()))
        self.assertEqual(attested_status(token), status_of("s1"))


@override_settings(
    GOVEX_REDIRECT_URI="http://testserver/api/auth/oidc/callback/",
    FRONTEND_URL="http://frontend",
)
class CallbackConsentPushTests(TestCase):
    def login(self, userinfo):
        self.client.get("/api/auth/oidc/login/")
        state = self.client.session["govex_oauth_state"]
        with (
            mock.patch("accounts.oidc.fetch_userinfo", return_value=userinfo),
            mock.patch("accounts.oidc.push_to_govex") as push,
        ):
            self.client.get(f"/api/auth/oidc/callback/?code=abc&state={state}")
        return push

    def test_pushes_when_govex_is_outdated(self):
        UserConsent.objects.create(user=govex_user("jonas", "s1"), terms=True)
        push = self.login({"sub": "s1", "preferred_username": "jonas", "attestations": {}})
        push.assert_called_once_with("s1")

    def test_skips_push_without_any_consent(self):
        push = self.login({"sub": "s1", "preferred_username": "jonas"})
        push.assert_not_called()
