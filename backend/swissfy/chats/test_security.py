import base64
from datetime import timedelta

from cryptography.exceptions import InvalidTag
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from swissfy.accounts.models import get_or_create_profile
from swissfy.moderation.models import Reason, Suspension, Warning

from .crypto import unwrap_message_key, wrap_message_key
from .models import ChatKey, ChatRequest, Envelope, Message
from .tests import MESSAGE_KEY, PUBLIC_KEY

User = get_user_model()


@override_settings(CHAT_SLOW_MODE_SECONDS=0)
class ChatSecurityTests(TestCase):
    def setUp(self):
        self.jonas = User.objects.create(username="jonas")
        self.anna = User.objects.create(username="anna")
        self.eve = User.objects.create(username="eve")
        ChatRequest.objects.create(sender=self.jonas, recipient=self.anna, status="accepted")
        self.client.force_login(self.jonas)

    def as_user(self, user):
        self.client.force_login(user)

    def payload(self, keys=(), message_key=True, **overrides):
        data = {
            "ciphertext": "Y2lwaGVy",
            "iv": "aXY=",
            "envelopes": [
                {
                    "key": key.pk,
                    "kem": "a2Vt",
                    "ecdh": PUBLIC_KEY["ecdh"],
                    "wrapped": "d3JhcHBlZA==",
                    "iv": "aXY=",
                }
                for key in keys
            ],
            **overrides,
        }
        if message_key:
            data["message_key"] = MESSAGE_KEY
        return data

    def send(self, payload, username="anna"):
        return self.client.post(
            f"/api/chats/{username}/messages/", payload, content_type="application/json"
        )

    def device_key(self, user):
        profile = get_or_create_profile(user)
        profile.chat_protection = "device"
        profile.save()
        return ChatKey.objects.create(user=user, kind="device", public_key=PUBLIC_KEY)

    def test_third_parties_cannot_read_a_conversation(self):
        self.assertEqual(self.send(self.payload()).status_code, 201)
        self.as_user(self.eve)
        with_anna = self.client.get("/api/chats/anna/messages/").json()["messages"]
        with_jonas = self.client.get("/api/chats/jonas/messages/").json()["messages"]
        self.assertEqual((with_anna, with_jonas), ([], []))
        conversations = self.client.get("/api/chats/conversations/").json()
        self.assertEqual(conversations, [])

    def test_reading_marks_nothing_for_third_parties(self):
        self.send(self.payload())
        self.as_user(self.eve)
        self.client.post(
            "/api/chats/anna/receive/", {"read": True}, content_type="application/json"
        )
        self.client.post("/api/chats/delivered/")
        message = Message.objects.get()
        self.assertIsNone(message.delivered_at)
        self.assertIsNone(message.read_at)

    def test_only_own_envelopes_are_returned(self):
        jonas_key = self.device_key(self.jonas)
        anna_key = self.device_key(self.anna)
        self.send(self.payload([jonas_key, anna_key], message_key=False))
        messages = self.client.get("/api/chats/anna/messages/").json()["messages"]
        self.assertEqual([envelope["key"] for envelope in messages[0]["envelopes"]], [jonas_key.pk])

    def test_cannot_message_without_accepted_request(self):
        self.as_user(self.eve)
        self.assertEqual(self.send(self.payload()).status_code, 403)
        ChatRequest.objects.create(sender=self.eve, recipient=self.anna)
        self.assertEqual(self.send(self.payload()).status_code, 403)
        ChatRequest.objects.filter(sender=self.eve).update(status="declined")
        self.assertEqual(self.send(self.payload()).status_code, 403)
        self.assertFalse(Message.objects.filter(sender=self.eve).exists())

    def test_cannot_message_self(self):
        self.assertEqual(self.send(self.payload(), "jonas").status_code, 404)

    def test_cannot_message_inactive_users(self):
        User.objects.filter(pk=self.anna.pk).update(is_active=False)
        self.assertEqual(self.send(self.payload(), "anna").status_code, 404)

    def test_cannot_message_unknown_users(self):
        self.assertEqual(self.send(self.payload(), "nobody").status_code, 404)

    def test_cannot_message_injected_usernames(self):
        self.assertEqual(self.send(self.payload(), "' OR 1=1--").status_code, 404)

    def test_cannot_accept_requests_addressed_to_someone_else(self):
        ChatRequest.objects.create(sender=self.eve, recipient=self.anna)
        response = self.client.post("/api/chats/eve/request/accept/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(ChatRequest.objects.get(sender=self.eve).status, "pending")

    def test_recipient_cannot_be_forced_to_accept_by_the_sender(self):
        ChatRequest.objects.create(sender=self.eve, recipient=self.anna)
        self.as_user(self.eve)
        self.assertEqual(self.client.post("/api/chats/anna/request/accept/").status_code, 404)
        self.assertEqual(ChatRequest.objects.get(sender=self.eve).status, "pending")

    def test_declined_sender_cannot_simply_retry(self):
        ChatRequest.objects.create(sender=self.eve, recipient=self.anna, status="declined")
        self.as_user(self.eve)
        self.assertEqual(self.client.post("/api/chats/anna/request/").status_code, 409)

    def test_chat_requests_respect_the_recipients_setting(self):
        profile = get_or_create_profile(self.anna)
        profile.chat_requests = False
        profile.save()
        self.as_user(self.eve)
        self.assertEqual(self.client.post("/api/chats/anna/request/").status_code, 403)

    def test_withdraw_only_deletes_own_messages(self):
        ChatRequest.objects.create(sender=self.eve, recipient=self.anna)
        Message.objects.create(sender=self.jonas, recipient=self.anna, ciphertext="a", iv="b")
        self.as_user(self.eve)
        self.client.post("/api/chats/anna/request/withdraw/")
        self.assertTrue(Message.objects.filter(sender=self.jonas).exists())

    def assert_envelopes_rejected(self, *owners):
        keys = {user.username: self.device_key(user) for user in (self.jonas, self.anna, self.eve)}
        envelope_keys = [keys[owner.username] for owner in owners]
        response = self.send(self.payload(envelope_keys, message_key=False))
        self.assertEqual(response.status_code, 409)
        self.assertFalse(Envelope.objects.filter(key=keys["eve"]).exists())

    def test_envelopes_including_a_third_party_are_rejected(self):
        self.assert_envelopes_rejected(self.jonas, self.anna, self.eve)

    def test_envelopes_replacing_the_recipient_are_rejected(self):
        self.assert_envelopes_rejected(self.jonas, self.eve)

    def test_envelopes_only_for_a_third_party_are_rejected(self):
        self.assert_envelopes_rejected(self.eve)

    def test_message_without_envelopes_is_rejected(self):
        self.assert_envelopes_rejected()

    def test_deactivated_keys_cannot_be_used(self):
        old = self.device_key(self.anna)
        old.active = False
        old.save()
        new = self.device_key(self.anna)
        jonas_key = self.device_key(self.jonas)
        response = self.send(self.payload([jonas_key, old], message_key=False))
        self.assertEqual(response.status_code, 409)
        response = self.send(self.payload([jonas_key, new], message_key=False))
        self.assertEqual(response.status_code, 201)

    def test_server_key_cannot_be_smuggled_into_end_to_end_chats(self):
        jonas_key = self.device_key(self.jonas)
        anna_key = self.device_key(self.anna)
        response = self.send(self.payload([jonas_key, anna_key], message_key=True))
        self.assertEqual(response.status_code, 409)
        self.assertFalse(Message.objects.filter(server_key__isnull=False).exists())

    def test_standard_chats_cannot_skip_the_server_key(self):
        self.assertEqual(self.send(self.payload(message_key=False)).status_code, 409)

    def test_suspended_users_cannot_chat(self):
        warning = Warning.objects.create(user=self.jonas, reason=Reason.values[0])
        Suspension.start(self.jonas, warning, 0, timezone.now())
        self.assertEqual(self.send(self.payload()).status_code, 403)
        self.assertEqual(self.client.post("/api/chats/eve/request/").status_code, 403)

    def assert_message_rejected(self, **overrides):
        self.assertEqual(self.send(self.payload(**overrides)).status_code, 400)

    def test_ciphertext_must_be_base64(self):
        self.assert_message_rejected(ciphertext="not base64!")

    def test_ciphertext_length_is_limited(self):
        self.assert_message_rejected(ciphertext="A" * 20004)

    def test_iv_length_is_limited(self):
        self.assert_message_rejected(iv="A" * 40)

    def test_iv_rejects_injections(self):
        self.assert_message_rejected(iv="' OR 1=1--")

    def test_ciphertext_must_be_a_string(self):
        self.assert_message_rejected(ciphertext={"$gt": ""})

    def test_envelopes_must_be_a_list(self):
        self.assert_message_rejected(envelopes="x")

    def assert_message_key_rejected(self, key):
        response = self.send(self.payload() | {"message_key": key})
        self.assertEqual(response.status_code, 400)

    def test_short_message_key_is_rejected(self):
        self.assert_message_key_rejected(base64.b64encode(bytes(16)).decode())

    def test_long_message_key_is_rejected(self):
        self.assert_message_key_rejected(base64.b64encode(bytes(33)).decode())

    def test_message_key_must_be_base64(self):
        self.assert_message_key_rejected("not base64")

    def test_empty_message_key_is_rejected(self):
        self.assert_message_key_rejected("")

    def assert_public_key_rejected(self, ecdh, kem="a2Vt"):
        response = self.client.put(
            "/api/chats/protection/",
            {"mode": "device", "key": {"public_key": {"ecdh": ecdh, "kem": kem}}},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_rsa_public_key_is_rejected(self):
        self.assert_public_key_rejected({"kty": "RSA", "crv": "P-256", "x": "a", "y": "b"})

    def test_other_curves_are_rejected(self):
        self.assert_public_key_rejected({"kty": "EC", "crv": "P-384", "x": "a", "y": "b"})

    def test_numeric_coordinates_are_rejected(self):
        self.assert_public_key_rejected({"kty": "EC", "crv": "P-256", "x": 1, "y": "b"})

    def test_ecdh_must_be_an_object(self):
        self.assert_public_key_rejected("x")

    def test_kem_must_be_base64(self):
        self.assert_public_key_rejected(PUBLIC_KEY["ecdh"], kem="!!")

    def test_kem_length_is_limited(self):
        self.assert_public_key_rejected(PUBLIC_KEY["ecdh"], kem="A" * 3000)

    def test_public_keys_are_stripped(self):
        extra = {**PUBLIC_KEY["ecdh"], "d": "private-part", "evil": "<script>"}
        self.client.put(
            "/api/chats/protection/",
            {"mode": "device", "key": {"public_key": {"ecdh": extra, "kem": "a2Vt"}}},
            content_type="application/json",
        )
        stored = ChatKey.objects.get(user=self.jonas, active=True).public_key["ecdh"]
        self.assertEqual(set(stored), {"kty", "crv", "x", "y"})

    def test_pin_secrets_are_only_given_to_their_owner(self):
        ChatKey.objects.create(
            user=self.anna,
            kind="pin",
            public_key=PUBLIC_KEY,
            wrapped_private_key="c2VjcmV0",
            salt="c2FsdA==",
            iv="aXY=",
        )
        keys = self.client.get("/api/chats/anna/keys/").content.decode()
        self.assertNotIn("c2VjcmV0", keys)
        self.assertNotIn("wrapped_private_key", keys)
        self.assertIsNone(self.client.get("/api/chats/protection/").json()["pin_key"])

    def test_device_keys_need_device_mode(self):
        response = self.client.post(
            "/api/chats/keys/", {"public_key": PUBLIC_KEY}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_expired_messages_are_not_returned(self):
        old = Message.objects.create(sender=self.anna, recipient=self.jonas, ciphertext="a", iv="b")
        Message.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=30))
        self.assertEqual(self.client.get("/api/chats/anna/messages/").json()["messages"], [])

    def test_slow_mode_cannot_be_bypassed(self):
        with override_settings(CHAT_SLOW_MODE_SECONDS=60):
            self.assertEqual(self.send(self.payload()).status_code, 201)
            response = self.send(self.payload())
            self.assertEqual(response.status_code, 429)
            self.assertIn("Retry-After", response)


class ServerKeyTests(TestCase):
    def setUp(self):
        self.jonas = User.objects.create(username="jonas")
        self.anna = User.objects.create(username="anna")
        self.eve = User.objects.create(username="eve")

    def message(self, sender, recipient):
        return Message(sender=sender, recipient=recipient, ciphertext="a", iv="b")

    def test_message_key_is_never_stored_in_plain(self):
        key = bytes(range(32))
        message = self.message(self.jonas, self.anna)
        message.server_key = wrap_message_key(message, key)
        self.assertNotIn(key, bytes(message.server_key))
        self.assertEqual(unwrap_message_key(message), key)

    def assert_wrapped_key_unusable_for(self, sender, recipient):
        message = self.message(self.jonas, self.anna)
        moved = self.message(sender, recipient)
        moved.server_key = wrap_message_key(message, bytes(32))
        with self.assertRaises(InvalidTag):
            unwrap_message_key(moved)

    def test_wrapped_key_is_bound_to_the_sender(self):
        self.assert_wrapped_key_unusable_for(self.eve, self.anna)

    def test_wrapped_key_is_bound_to_the_recipient(self):
        self.assert_wrapped_key_unusable_for(self.jonas, self.eve)

    def test_wrapped_key_is_bound_to_the_direction(self):
        self.assert_wrapped_key_unusable_for(self.anna, self.jonas)

    def test_tampered_wrapped_key_is_rejected(self):
        message = self.message(self.jonas, self.anna)
        wrapped = bytearray(wrap_message_key(message, bytes(32)))
        wrapped[-1] ^= 1
        message.server_key = bytes(wrapped)
        with self.assertRaises(InvalidTag):
            unwrap_message_key(message)

    def test_every_wrap_uses_a_fresh_nonce(self):
        message = self.message(self.jonas, self.anna)
        first = wrap_message_key(message, bytes(32))
        second = wrap_message_key(message, bytes(32))
        self.assertNotEqual(first[:12], second[:12])
