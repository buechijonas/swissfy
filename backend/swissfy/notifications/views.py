from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from commons.views import BaseViewSet
from main.pagination import NextPagePagination

from .models import Notification
from .notify import syncs_expired_warnings
from .serializers import NotificationModelSerializer


class NotificationViewSet(BaseViewSet, mixins.ListModelMixin):
    serializer_class = NotificationModelSerializer
    pagination_class = NextPagePagination

    def get_queryset(self):
        return Notification.objects.apply_acl(self.request.user).with_details()

    @syncs_expired_warnings
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=False)
    @syncs_expired_warnings
    def unread(self, request):
        unread = Notification.objects.apply_acl(request.user).unread()
        return Response({"count": unread.count()})

    @action(detail=False, methods=["post"], url_path="read")
    def mark_read(self, request):
        Notification.objects.apply_acl(request.user).mark_read()
        return Response({"count": 0})
