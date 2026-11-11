from rest_framework import serializers

from commons.serializers import BaseModelSerializer
from swissfy.posts.serializers import AuthorModelSerializer

from .models import Notification


class NotificationModelSerializer(BaseModelSerializer):
    class read(BaseModelSerializer.read):
        actor = AuthorModelSerializer.read(read_only=True)
        message = serializers.CharField(read_only=True)
        link = serializers.CharField(read_only=True, allow_null=True)
        read = serializers.BooleanField(source="is_read", read_only=True)
        request = serializers.CharField(source="request_state", read_only=True, allow_null=True)

        class Meta(BaseModelSerializer.read.Meta):
            model = Notification
            fields = ["id", "kind", "actor", "message", "link", "created_at", "read", "request"]
