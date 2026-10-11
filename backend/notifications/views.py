from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from main.pagination import NextPagePagination

from .models import Notification
from .notify import sync_expired_warnings
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    pagination_class = NextPagePagination

    def get_queryset(self):
        user = self.request.user
        sync_expired_warnings(user)
        return (
            Notification.objects.filter(recipient=user)
            .select_related(
                "recipient",
                "actor__profile",
                "post",
                "comment",
                "warning",
                "suspension",
            )
            .prefetch_related("actor__groups")
        )


class UnreadCountView(APIView):
    def get(self, request):
        sync_expired_warnings(request.user)
        unread = Notification.objects.filter(recipient=request.user, read_at=None)
        return Response({"count": unread.count()})


class ReadView(APIView):
    def post(self, request):
        Notification.objects.filter(recipient=request.user, read_at=None).update(
            read_at=timezone.now()
        )
        return Response({"count": 0})
