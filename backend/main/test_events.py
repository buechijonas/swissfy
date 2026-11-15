import asyncio
from unittest import mock

import psycopg
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase, override_settings

from commons.events import CHANNEL, QUEUE_SIZE, SYNC, Hub, conninfo, enqueue, notify
from swissfy.accounts.models import get_or_create_profile
from swissfy.chats.models import ChatRequest, Message
from swissfy.notifications.models import Notification
from swissfy.posts.models import Post

User = get_user_model()

TIMEOUT = 5


@override_settings(CHAT_SLOW_MODE_SECONDS=0)
class PublishTests(TransactionTestCase):
    def setUp(self):
        self.anna = User.objects.create(username="anna")
        self.jonas = User.objects.create(username="jonas")
        get_or_create_profile(self.anna)
        get_or_create_profile(self.jonas)
        self.listener = psycopg.connect(conninfo(), autocommit=True)
        self.listener.execute(f"LISTEN {CHANNEL}")
        self.addCleanup(self.listener.close)

    def received(self):
        notifications = self.listener.notifies(timeout=0.5)
        return [notification.payload for notification in notifications]

    def event(self, kind, *users):
        return f'{{"users": [{", ".join(str(user.pk) for user in users)}], "kind": "{kind}"}}'

    def test_message_notifies_both_participants(self):
        Message.objects.create(sender=self.anna, recipient=self.jonas, ciphertext="x", iv="y")
        self.assertEqual(self.received(), [self.event("chat", self.anna, self.jonas)])

    def test_receiving_notifies_participants_until_nothing_changes(self):
        ChatRequest.objects.create(sender=self.anna, recipient=self.jonas, status="accepted")
        Message.objects.create(sender=self.anna, recipient=self.jonas, ciphertext="x", iv="y")
        self.received()
        self.client.force_login(self.jonas)

        self.client.post("/api/chats/anna/receive/", {"read": True}, "application/json")
        self.assertEqual(self.received(), [self.event("chat", self.anna, self.jonas)] * 2)
        self.client.post("/api/chats/anna/receive/", {"read": True}, "application/json")
        self.assertEqual(self.received(), [])

    def test_chat_request_notifies_both_sides(self):
        self.client.force_login(self.anna)
        self.client.post("/api/chats/jonas/request/")
        self.assertIn(self.event("chat", self.anna, self.jonas), self.received())

    def test_like_notifies_the_author(self):
        post = Post.objects.create(author=self.anna, text="Hallo")
        self.client.force_login(self.jonas)
        self.client.post(f"/api/posts/{post.uuid}/like/")
        self.assertEqual(self.received(), [self.event("notification", self.anna)])

    def test_marking_notifications_read_notifies_the_recipient(self):
        Notification.notify(self.anna, Notification.Kind.FOLLOW, actor=self.jonas)
        self.received()
        Notification.objects.filter(recipient=self.anna).mark_read()
        self.assertEqual(self.received(), [self.event("notification", self.anna)])

    def test_nothing_is_sent_when_nothing_changed(self):
        Notification.objects.filter(recipient=self.anna).mark_read()
        Message.objects.filter(recipient=self.anna).mark_delivered()
        self.assertEqual(self.received(), [])


class StreamTests(TransactionTestCase):
    def setUp(self):
        self.anna = User.objects.create(username="anna")
        self.jonas = User.objects.create(username="jonas")
        self.hub = Hub()
        patcher = mock.patch("main.views.hub", self.hub)
        patcher.start()
        self.addCleanup(patcher.stop)

    async def next_chunk(self, content):
        return await asyncio.wait_for(anext(content), TIMEOUT)

    async def test_anonymous_users_get_no_stream(self):
        response = await self.async_client.get("/api/events/")
        self.assertEqual(response.status_code, 403)

    async def test_stream_delivers_only_own_events(self):
        await self.async_client.aforce_login(self.anna)
        response = await self.async_client.get("/api/events/")
        self.assertEqual(response["Content-Type"], "text/event-stream")
        content = aiter(response.streaming_content)
        try:
            self.assertEqual(await self.next_chunk(content), b"retry: 3000\n\n")
            self.assertEqual(await self.next_chunk(content), b"event: sync\ndata: {}\n\n")
            await sync_to_async(notify)([self.jonas.pk], "chat")
            await sync_to_async(notify)([self.anna.pk], "notification")
            self.assertEqual(await self.next_chunk(content), b"event: notification\ndata: {}\n\n")
        finally:
            self.hub.listener.cancel()

    async def test_stream_sends_heartbeats(self):
        await self.async_client.aforce_login(self.anna)
        with mock.patch("main.views.HEARTBEAT_SECONDS", 0.01):
            response = await self.async_client.get("/api/events/")
            content = aiter(response.streaming_content)
            try:
                await self.next_chunk(content)
                chunks = {await self.next_chunk(content) for _ in range(3)}
                self.assertIn(b": heartbeat\n\n", chunks)
            finally:
                self.hub.listener.cancel()

    async def test_stream_only_answers_get(self):
        await self.async_client.aforce_login(self.anna)
        response = await self.async_client.post("/api/events/")
        self.assertEqual(response.status_code, 405)


class HubTests(TransactionTestCase):
    def test_full_queue_collapses_into_one_sync(self):
        queue = asyncio.Queue(QUEUE_SIZE)
        for _ in range(QUEUE_SIZE + 1):
            enqueue(queue, "chat")
        self.assertEqual(queue.qsize(), 1)
        self.assertEqual(queue.get_nowait(), SYNC)

    def test_queue_keeps_events_while_there_is_room(self):
        queue = asyncio.Queue(QUEUE_SIZE)
        enqueue(queue, "chat")
        enqueue(queue, "notification")
        self.assertEqual([queue.get_nowait(), queue.get_nowait()], ["chat", "notification"])

    async def test_listener_survives_unexpected_errors(self):
        hub = Hub()
        calls = []
        stopped = asyncio.Event()

        async def receive():
            calls.append(1)
            if len(calls) == 1:
                raise ValueError("broken payload")
            await stopped.wait()

        with mock.patch.object(hub, "receive", receive), mock.patch(
            "commons.events.RECONNECT_SECONDS", 0
        ):
            hub.subscribe(1)
            await asyncio.sleep(0.05)
            self.assertEqual(len(calls), 2)
            self.assertFalse(hub.listener.done())
            hub.listener.cancel()

    async def test_finished_listener_is_restarted_on_subscribe(self):
        hub = Hub()
        with mock.patch.object(hub, "listen", mock.AsyncMock()):
            hub.subscribe(1)
            first = hub.listener
            await first
            hub.subscribe(2)
            self.assertIsNot(hub.listener, first)
