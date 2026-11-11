from django.utils import timezone
from rest_framework import serializers

from .models import Reason, Suspension, Warning
from .sanctions import SUSPENSION_STEPS, warning_expires_at


def reason_options():
    return [{"value": value, "label": label} for value, label in Reason.choices]


class WarningSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    reason = serializers.CharField(source="get_reason_display")
    target = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()
    expires_at = serializers.SerializerMethodField()
    expired = serializers.SerializerMethodField()
    caused_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Warning
        fields = [
            "id",
            "type",
            "reason",
            "created_at",
            "caused_at",
            "target",
            "link",
            "expires_at",
            "expired",
        ]

    def get_type(self, obj):
        return "warning"

    def get_expires_at(self, obj):
        return warning_expires_at(obj)

    def get_expired(self, obj):
        return warning_expires_at(obj) <= timezone.now()

    def get_target(self, obj):
        if obj.comment_id:
            return "Kommentar"
        return "Feed" if obj.post_id else None

    def get_link(self, obj):
        if not self.context.get("moderation"):
            return None
        if obj.comment_id:
            return f"/moderation/comments/{obj.comment.uuid}"
        return f"/moderation/posts/{obj.post.uuid}" if obj.post_id else None


class SuspensionSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source="starts_at")
    caused_at = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()

    class Meta:
        model = Suspension
        fields = ["id", "type", "created_at", "caused_at", "ends_at", "duration", "state"]

    def get_caused_at(self, obj):
        moment = obj.warning.created_at if obj.warning else obj.starts_at
        return serializers.DateTimeField().to_representation(moment)

    def get_type(self, obj):
        return "suspension"

    def get_duration(self, obj):
        return SUSPENSION_STEPS[obj.step][1]

    def get_state(self, obj):
        now = timezone.now()
        if obj.starts_at > now:
            return "scheduled"
        return "ended" if obj.ends_at and obj.ends_at <= now else "active"
