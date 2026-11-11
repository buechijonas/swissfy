from rest_framework import mixins
from rest_framework.response import Response

from commons.views import BaseViewSet
from main.pagination import NextPagePagination

from .models import Notification
from .notify import sync_expired_warnings
from .serializers import NotificationModelSerializer


class NotificationViewSet(BaseViewSet, mixins.ListModelMixin):
    serializer_class = NotificationModelSerializer
    pagination_class = NextPagePagination

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        sync_expired_warnings(request.user)

    def get_queryset(self):
        return Notification.objects.apply_acl(self.request.user).with_details()

    def unread(self, request):
        unread = Notification.objects.apply_acl(request.user).unread()
        return Response({"count": unread.count()})

    def mark_read(self, request):
        Notification.objects.apply_acl(request.user).mark_read()
        return Response({"count": 0})
