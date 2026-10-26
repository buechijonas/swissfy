from rest_framework.pagination import CursorPagination


class NewestFirst(CursorPagination):
    page_size = 25
    ordering = "-id"


class FeedOrder(NewestFirst):
    ordering = ("-day", "-viewer_is_friend", "-shown_at", "-id")


class SavedOrder(NewestFirst):
    ordering = "-saved_at"


class OldestFirst(CursorPagination):
    page_size = 50
    ordering = "created_at"
