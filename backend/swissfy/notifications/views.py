from functools import wraps

from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from commons.views import BaseViewSet
from main.pagination import NextPagePagination

from .models import Notification
from .serializers import NotificationModelSerializer


def syncs_expired_warnings(view_action):
    @wraps(view_action)
    def wrapper(self, request, *args, **kwargs):
        Notification.objects.sync_expired_warnings(request.user)
        return view_action(self, request, *args, **kwargs)

    return wrapper


class NotificationViewSet(BaseViewSet, mixins.ListModelMixin):
    serializer_class = NotificationModelSerializer
    pagination_class = NextPagePagination

    def get_queryset(self):
        user = self.request.user
        return Notification.objects.apply_acl(user).with_details(user)

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
