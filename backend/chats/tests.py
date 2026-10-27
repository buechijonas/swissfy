import base64
from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import get_or_create_profile

from .models import ChatKey, ChatRequest, Envelope, Message

User = get_user_model()

PUBLIC_KEY = {"ecdh": {"kty": "EC", "crv": "P-256", "x": "abc", "y": "def"}, "kem": "a2Vt"}
MESSAGE_KEY = base64.b64encode(bytes(range(32))).decode()


class ChatTests(TestCase):
    def setUp(self):
        slow_mode = override_settings(CHAT_SLOW_MODE_SECONDS=0)
        slow_mode.enable()
        self.addCleanup(slow_mode.disable)
        self.jonas = User.objects.create(username="jonas")
        self.anna = User.objects.create(username="anna")
        self.eve = User.objects.create(username="eve")
        for sender, recipient in [
            (self.jonas, self.anna),
            (self.jonas, self.eve),
            (self.eve, self.anna),
        ]:
            ChatRequest.objects.create(sender=sender, recipient=recipient, status="accepted")
        self.client.force_login(self.jonas)

    def set_mode(self, user, mode):
        profile = get_or_create_profile(user)
        profile.chat_protection = mode
        profile.save()
        if mode == "standard":
            return None
        return ChatKey.objects.create(user=user, kind=mode, public_key=PUBLIC_KEY)

    def put_protection(self, payload):
        return self.client.put("/api/chats/protection/", payload, content_type="application/json")

    def payload(self, keys=(), message_key=True):
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
        }
        if message_key:
            data["message_key"] = MESSAGE_KEY
        return data

    def send(self, payload, username="anna"):
        return self.client.post(
            f"/api/chats/{username}/messages/", payload, content_type="application/json"
        )

    def messages(self, username="anna", read=False):
        url = f"/api/chats/{username}/messages/" + ("?read=true" if read else "")
        return self.client.get(url).json()["messages"]

    def statuses(self, username="anna"):
        return self.client.get(f"/api/chats/{username}/messages/").json()["statuses"]

    def test_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.get("/api/chats/protection/").status_code, 403)

    def test_default_protection_is_standard(self):
        data = self.client.get("/api/chats/protection/").json()
        self.assertEqual(data, {"mode": "standard", "keys": [], "pin_key": None})

    def test_switch_to_device(self):
        data = self.put_protection({"mode": "device", "key": {"public_key": PUBLIC_KEY}}).json()
        self.assertEqual(data["mode"], "device")
        self.assertEqual([key["kind"] for key in data["keys"]], ["device"])
        self.assertIsNone(data["pin_key"])

    def test_switch_to_pin_replaces_old_keys(self):
        old = self.set_mode(self.jonas, "device")
        data = self.put_protection(
            {
                "mode": "pin",
                "key": {
                    "public_key": PUBLIC_KEY,
                    "wrapped_private_key": "c2VjcmV0",
                    "salt": "c2FsdA==",
                    "iv": "aXY=",
                },
            }
        ).json()
        self.assertEqual(data["pin_key"]["wrapped_private_key"], "c2VjcmV0")
        old.refresh_from_db()
        self.assertFalse(old.active)

    def test_pin_needs_wrapped_key(self):
        response = self.put_protection({"mode": "pin", "key": {"public_key": PUBLIC_KEY}})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(get_or_create_profile(self.jonas).chat_protection, "standard")

    def test_standard_takes_no_key(self):
        response = self.put_protection({"mode": "standard", "key": {"public_key": PUBLIC_KEY}})
        self.assertEqual(response.status_code, 400)

    def test_device_key_only_in_device_mode(self):
        url = "/api/chats/keys/"
        payload = {"public_key": PUBLIC_KEY}
        self.assertEqual(
            self.client.post(url, payload, content_type="application/json").status_code, 400
        )
        self.set_mode(self.jonas, "device")
        self.assertEqual(
            self.client.post(url, payload, content_type="application/json").status_code, 201
        )

    def test_conversation_keys(self):
        self.set_mode(self.anna, "device")
        self.set_mode(self.eve, "device")
        data = self.client.get("/api/chats/anna/keys/").json()
        self.assertEqual(len(data["keys"]), 1)
        self.assertTrue(data["server_key"])

        self.set_mode(self.jonas, "pin")
        data = self.client.get("/api/chats/anna/keys/").json()
        self.assertEqual(len(data["keys"]), 2)
        self.assertFalse(data["server_key"])

    def test_no_conversation_with_self(self):
        self.assertEqual(self.client.get("/api/chats/jonas/keys/").status_code, 404)

    def test_standard_chat_is_stored_encrypted(self):
        self.assertEqual(self.send(self.payload()).status_code, 201)
        message = Message.objects.get()
        self.assertNotIn(bytes(range(32)), bytes(message.server_key))

        data = self.messages()
        self.assertEqual(data[0]["sender"], "jonas")
        self.assertEqual(data[0]["message_key"], MESSAGE_KEY)

        self.client.force_login(self.anna)
        self.assertEqual(self.messages("jonas")[0]["message_key"], MESSAGE_KEY)

    def test_end_to_end_chat_has_no_server_key(self):
        jonas_key = self.set_mode(self.jonas, "device")
        anna_key = self.set_mode(self.anna, "pin")
        self.assertEqual(self.send(self.payload([jonas_key, anna_key], False)).status_code, 201)
        self.assertIsNone(Message.objects.get().server_key)

        data = self.messages()
        self.assertIsNone(data[0]["message_key"])
        self.assertEqual([e["key"] for e in data[0]["envelopes"]], [jonas_key.pk])

        self.client.force_login(self.anna)
        self.assertEqual([e["key"] for e in self.messages("jonas")[0]["envelopes"]], [anna_key.pk])

    def test_mixed_chat_needs_server_key(self):
        anna_key = self.set_mode(self.anna, "device")
        response = self.send(self.payload([anna_key], False))
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.send(self.payload([anna_key])).status_code, 201)

    def test_end_to_end_chat_rejects_server_key(self):
        jonas_key = self.set_mode(self.jonas, "device")
        anna_key = self.set_mode(self.anna, "device")
        self.assertEqual(self.send(self.payload([jonas_key, anna_key])).status_code, 409)

    def test_send_needs_all_active_keys(self):
        jonas_key = self.set_mode(self.jonas, "device")
        anna_key = self.set_mode(self.anna, "device")
        eve_key = self.set_mode(self.eve, "device")
        self.assertEqual(self.send(self.payload([jonas_key], False)).status_code, 409)
        self.assertEqual(
            self.send(self.payload([jonas_key, anna_key, eve_key], False)).status_code, 409
        )
        self.assertFalse(Message.objects.exists())

    def test_other_conversations_stay_hidden(self):
        self.client.force_login(self.eve)
        self.send(self.payload())
        self.client.force_login(self.jonas)
        self.assertEqual(self.messages(), [])

    def test_messages_after(self):
        self.send(self.payload())
        self.send(self.payload())
        first = Message.objects.first()
        data = self.client.get(f"/api/chats/anna/messages/?after={first.pk}").json()
        self.assertEqual(len(data["messages"]), 1)
        self.assertEqual(self.client.get("/api/chats/anna/messages/?after=x").status_code, 400)

    def test_invalid_message_key(self):
        payload = self.payload()
        payload["message_key"] = "c2hvcnQ="
        self.assertEqual(self.send(payload).status_code, 400)

    def status(self):
        return self.statuses()[str(Message.objects.get().pk)]

    def test_sent_delivered_read(self):
        self.send(self.payload())
        self.assertEqual(self.status(), "sent")
        self.assertEqual(self.messages()[0]["status"], "sent")

        self.client.force_login(self.anna)
        self.client.post("/api/chats/delivered/")
        self.client.force_login(self.jonas)
        self.assertEqual(self.status(), "delivered")

        self.client.force_login(self.anna)
        self.assertIsNone(self.messages("jonas", read=True)[0]["status"])
        self.client.force_login(self.jonas)
        self.assertEqual(self.status(), "read")

    def test_opening_chat_in_background_only_delivers(self):
        self.send(self.payload())
        self.client.force_login(self.anna)
        self.messages("jonas")
        self.client.force_login(self.jonas)
        self.assertEqual(self.status(), "delivered")

    def test_recipient_without_read_receipts_is_never_read(self):
        profile = get_or_create_profile(self.anna)
        profile.read_receipts = False
        profile.save()
        self.send(self.payload())
        self.client.force_login(self.anna)
        self.messages("jonas", read=True)
        self.assertIsNone(Message.objects.get().read_at)
        self.assertIsNotNone(Message.objects.get().seen_at)

        profile.read_receipts = True
        profile.save()
        self.client.force_login(self.jonas)
        self.assertEqual(self.status(), "delivered")

    def test_sender_without_read_receipts_sees_no_reads(self):
        self.send(self.payload())
        self.client.force_login(self.anna)
        self.messages("jonas", read=True)

        profile = get_or_create_profile(self.jonas)
        profile.read_receipts = False
        profile.save()
        self.client.force_login(self.jonas)
        self.assertEqual(self.status(), "delivered")

    def test_old_messages_are_hidden_and_deleted(self):
        self.send(self.payload())
        self.send(self.payload())
        old = Message.objects.first()
        Message.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=15))

        self.assertEqual(len(self.messages()), 1)
        self.assertNotIn(str(old.pk), self.statuses())

        call_command("delete_old_messages", stdout=StringIO())
        self.assertEqual(Message.objects.count(), 1)
        self.assertFalse(Envelope.objects.filter(message_id=old.pk).exists())

    @override_settings(CHAT_SLOW_MODE_SECONDS=5)
    def test_slow_mode(self):
        self.assertEqual(self.send(self.payload()).json(), {"retry_after": 5})
        response = self.send(self.payload())
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Retry-After"], "5")
        self.assertEqual(Message.objects.count(), 1)

        self.assertEqual(self.send(self.payload(), "eve").status_code, 201)

        Message.objects.update(created_at=timezone.now() - timedelta(seconds=5))
        self.assertEqual(self.send(self.payload()).status_code, 201)


class ChatRequestTests(TestCase):
    def setUp(self):
        slow_mode = override_settings(CHAT_SLOW_MODE_SECONDS=0)
        slow_mode.enable()
        self.addCleanup(slow_mode.disable)
        self.jonas = User.objects.create(username="jonas")
        self.anna = User.objects.create(username="anna")
        self.client.force_login(self.jonas)

    def send(self, username="anna"):
        return self.client.post(
            f"/api/chats/{username}/messages/",
            {"ciphertext": "Y2lwaGVy", "iv": "aXY=", "envelopes": [], "message_key": MESSAGE_KEY},
            content_type="application/json",
        )

    def request_chat(self, username="anna"):
        return self.client.post(f"/api/chats/{username}/request/")

    def accept(self, username="jonas"):
        return self.client.post(f"/api/chats/{username}/request/accept/")

    def state(self, username="anna"):
        return self.client.get(f"/api/chats/{username}/messages/").json()["chat_request"]

    def test_no_messages_without_request(self):
        self.assertIsNone(self.state())
        self.assertEqual(self.send().status_code, 403)
        self.assertFalse(Message.objects.exists())

    def test_send_request(self):
        response = self.request_chat()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"status": "pending", "incoming": False})
        self.assertEqual(self.send().status_code, 403)

    def test_only_one_side_can_request(self):
        self.request_chat()
        self.client.force_login(self.anna)
        self.assertEqual(self.state("jonas"), {"status": "pending", "incoming": True})
        self.assertEqual(self.request_chat("jonas").status_code, 409)
        self.assertEqual(self.send("jonas").status_code, 403)
        self.assertEqual(ChatRequest.objects.count(), 1)

    def test_request_list(self):
        self.request_chat()
        self.client.force_login(self.anna)
        requests = self.client.get("/api/chats/requests/").json()
        self.assertEqual([user["username"] for user in requests], ["jonas"])

    def test_accept(self):
        self.request_chat()
        self.client.force_login(self.anna)
        self.assertEqual(self.accept().json(), {"status": "accepted", "incoming": True})
        self.assertEqual(self.client.get("/api/chats/requests/").json(), [])
        self.assertEqual(self.send("jonas").status_code, 201)

        self.client.force_login(self.jonas)
        self.assertEqual(self.send().status_code, 201)

    def test_sender_cannot_accept_own_request(self):
        self.request_chat()
        self.assertEqual(self.accept("anna").status_code, 404)

    def test_decline_blocks_sender(self):
        self.request_chat()
        self.client.force_login(self.anna)
        response = self.client.delete("/api/chats/jonas/request/")
        self.assertEqual(response.json()["status"], "declined")
        self.assertEqual(self.send("jonas").status_code, 403)

        self.client.force_login(self.jonas)
        self.assertEqual(self.state(), {"status": "declined", "incoming": False})
        self.assertEqual(self.request_chat().status_code, 409)
        self.assertEqual(self.send().status_code, 403)

    def test_withdraw(self):
        self.request_chat()
        response = self.client.post("/api/chats/anna/request/withdraw/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ChatRequest.objects.exists())
        self.assertIsNone(self.state())

        self.assertEqual(self.request_chat().status_code, 201)

    def test_only_sender_can_withdraw_pending(self):
        self.request_chat()
        self.client.force_login(self.anna)
        self.assertEqual(self.client.post("/api/chats/jonas/request/withdraw/").status_code, 404)
        self.accept()

        self.client.force_login(self.jonas)
        self.assertEqual(self.client.post("/api/chats/anna/request/withdraw/").status_code, 404)
        self.assertTrue(ChatRequest.objects.exists())

    def test_decliner_can_lift_block_with_new_request(self):
        self.request_chat()
        self.client.force_login(self.anna)
        self.client.delete("/api/chats/jonas/request/")

        response = self.request_chat("jonas")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"status": "pending", "incoming": False})
        self.assertEqual(ChatRequest.objects.count(), 1)

        self.client.force_login(self.jonas)
        self.assertEqual(self.state(), {"status": "pending", "incoming": True})
        self.assertEqual(self.accept("anna").status_code, 200)
        self.assertEqual(self.send().status_code, 201)

    def test_requests_can_be_disabled(self):
        profile = get_or_create_profile(self.anna)
        profile.chat_requests = False
        profile.save()
        data = self.client.get("/api/chats/anna/messages/").json()
        self.assertFalse(data["can_request"])
        self.assertEqual(self.request_chat().status_code, 403)
        self.assertFalse(ChatRequest.objects.exists())

    def test_can_request(self):
        data = self.client.get("/api/chats/anna/messages/").json()
        self.assertTrue(data["can_request"])
        self.request_chat()
        data = self.client.get("/api/chats/anna/messages/").json()
        self.assertFalse(data["can_request"])

    def test_conversations(self):
        eve = User.objects.create(username="eve")
        mia = User.objects.create(username="mia")
        self.request_chat()
        self.request_chat("eve")
        self.client.force_login(eve)
        self.accept()
        self.client.force_login(mia)
        self.request_chat("jonas")

        self.client.force_login(self.jonas)
        conversations = self.client.get("/api/chats/conversations/").json()
        self.assertEqual([user["username"] for user in conversations], ["eve", "anna"])

        self.assertIsNone(conversations[0]["last_message"])
        self.assertFalse(conversations[0]["pending"])
        self.assertTrue(conversations[1]["pending"])

        self.client.force_login(self.anna)
        self.client.post("/api/chats/jonas/request/accept/")
        self.send("jonas")
        self.client.force_login(self.jonas)
        conversations = self.client.get("/api/chats/conversations/").json()
        self.assertEqual([user["username"] for user in conversations], ["anna", "eve"])
        last = conversations[0]["last_message"]
        self.assertEqual((last["sender"], last["message_key"]), ("anna", MESSAGE_KEY))
        self.assertIsNone(last["status"])
        self.assertTrue(conversations[0]["unread"])
        self.client.get("/api/chats/anna/messages/?read=true")
        self.assertFalse(self.client.get("/api/chats/conversations/").json()[0]["unread"])

        self.send("eve")
        conversations = self.client.get("/api/chats/conversations/").json()
        self.assertEqual([user["username"] for user in conversations], ["eve", "anna"])
        self.assertEqual(conversations[0]["last_message"]["status"], "sent")
        self.assertFalse(conversations[0]["unread"])

    def unread(self):
        return sorted(self.client.post("/api/chats/delivered/").json()["unread"])

    def test_unread(self):
        eve = User.objects.create(username="eve")
        mia = User.objects.create(username="mia")
        for user in (self.anna, eve):
            self.request_chat(user.username)
            self.client.force_login(user)
            self.accept()
            self.send("jonas")
            self.send("jonas")
            self.client.force_login(self.jonas)
        self.client.force_login(mia)
        self.request_chat("jonas")
        self.send("jonas")

        self.client.force_login(self.jonas)
        self.assertEqual(self.unread(), ["anna", "eve"])
        self.client.get("/api/chats/anna/messages/?read=true")
        self.assertEqual(self.unread(), ["eve"])

    def archived(self):
        conversations = self.client.get("/api/chats/conversations/").json()
        return {user["username"]: user["archived"] for user in conversations}

    def test_archive(self):
        self.request_chat()
        self.client.force_login(self.anna)
        self.accept()
        self.send("jonas")

        self.client.force_login(self.jonas)
        self.assertEqual(self.archived(), {"anna": False})
        self.assertEqual(self.client.post("/api/chats/anna/archive/").json(), {"archived": True})
        self.client.post("/api/chats/anna/archive/")
        self.assertEqual(self.archived(), {"anna": True})
        self.assertEqual(self.unread(), [])

        self.client.force_login(self.anna)
        self.assertEqual(self.archived(), {"jonas": False})

        self.client.force_login(self.jonas)
        self.client.delete("/api/chats/anna/archive/")
        self.assertEqual(self.archived(), {"anna": False})
        self.assertEqual(self.unread(), ["anna"])
