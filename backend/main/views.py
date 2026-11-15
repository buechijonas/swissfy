import asyncio

from django.db import connection
from django.http import HttpResponseForbidden, JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_GET

from commons.events import hub

HEARTBEAT_SECONDS = 25
RETRY_MILLISECONDS = 3000


def health(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"status": "ok"})


async def stream(user):
    queue = hub.subscribe(user)
    try:
        yield f"retry: {RETRY_MILLISECONDS}\n\n"
        while True:
            try:
                kind = await asyncio.wait_for(queue.get(), HEARTBEAT_SECONDS)
            except TimeoutError:
                yield ": heartbeat\n\n"
            else:
                yield f"event: {kind}\ndata: {{}}\n\n"
    finally:
        hub.unsubscribe(user, queue)


@require_GET
async def events(request):
    user = await request.auser()
    if not user.is_authenticated or not user.is_active:
        return HttpResponseForbidden()
    return StreamingHttpResponse(
        stream(user.pk),
        content_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
