import asyncio
import json
import logging

import psycopg
from django.db import connection, transaction

CHANNEL = "swissfy_events"
RECONNECT_SECONDS = 2
QUEUE_SIZE = 32
SYNC = "sync"

logger = logging.getLogger(__name__)


def notify(users, kind):
    payload = json.dumps({"users": users, "kind": kind})
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_notify(%s, %s)", [CHANNEL, payload])


def publish(users, kind):
    users = sorted(set(users))
    if users:
        transaction.on_commit(lambda: notify(users, kind))


def conninfo():
    database = connection.settings_dict
    return psycopg.conninfo.make_conninfo(
        dbname=database["NAME"],
        user=database["USER"],
        password=database["PASSWORD"],
        host=database["HOST"],
        port=database["PORT"],
    )


def enqueue(queue, kind):
    if queue.full():
        while not queue.empty():
            queue.get_nowait()
        kind = SYNC
    queue.put_nowait(kind)


class Hub:
    def __init__(self):
        self.queues = {}
        self.listener = None

    def subscribe(self, user):
        queue = asyncio.Queue(QUEUE_SIZE)
        self.queues.setdefault(user, set()).add(queue)
        if self.listener is None or self.listener.done():
            self.listener = asyncio.create_task(self.listen())
        return queue

    def unsubscribe(self, user, queue):
        queues = self.queues[user]
        queues.discard(queue)
        if not queues:
            del self.queues[user]

    def deliver(self, users, kind):
        for user in users:
            for queue in self.queues.get(user, ()):
                enqueue(queue, kind)

    async def listen(self):
        while True:
            try:
                await self.receive()
            except Exception:
                logger.exception("Event listener failed, reconnecting.")
                await asyncio.sleep(RECONNECT_SECONDS)

    async def receive(self):
        async with await psycopg.AsyncConnection.connect(conninfo(), autocommit=True) as listener:
            await listener.execute(f"LISTEN {CHANNEL}")
            self.deliver(list(self.queues), SYNC)
            async for notification in listener.notifies():
                event = json.loads(notification.payload)
                self.deliver(event["users"], event["kind"])


hub = Hub()
