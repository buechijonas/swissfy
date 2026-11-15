from datetime import date, timedelta

from django.utils import timezone
from rest_framework.pagination import CursorPagination

from ..models import FeedEntry

FEED_WINDOW = timedelta(days=7)


class NewestFirst(CursorPagination):
    page_size = 25
    ordering = "-id"


class FeedOrder(NewestFirst):
    ordering = ("-day", "-viewer_is_friend", "-shown_at", "-id")

    def newest_day(self, request):
        cursor = self.decode_cursor(request)
        if cursor is None:
            return timezone.localdate()
        if cursor.reverse or cursor.position is None:
            return None
        return date.fromisoformat(cursor.position)

    def paginate_queryset(self, queryset, request, view=None):
        newest = self.newest_day(request)
        oldest = FeedEntry.objects.oldest_day()
        if newest is None or oldest is None:
            return super().paginate_queryset(queryset, request, view)
        window = FEED_WINDOW
        while True:
            lower = newest - window
            page = super().paginate_queryset(queryset.filter(day__gt=lower), request, view)
            if self.has_next or lower < oldest:
                return page
            window *= 2


class SavedOrder(NewestFirst):
    ordering = "-saved_at"


class OldestFirst(CursorPagination):
    page_size = 50
    ordering = "created_at"
