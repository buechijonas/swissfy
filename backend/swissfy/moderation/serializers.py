from rest_framework import serializers

from commons.serializers import BaseModelSerializer

from .models import Reason, Suspension, Warning

CHOOSE_REASON = "Wähle einen Grund."


class WarningModelSerializer(BaseModelSerializer):
    class read(BaseModelSerializer.read):
        type = serializers.CharField(source="event_type", read_only=True)
        reason = serializers.CharField(source="get_reason_display", read_only=True)
        caused_at = serializers.DateTimeField(source="created_at", read_only=True)
        target = serializers.CharField(source="target_label", read_only=True, allow_null=True)
        link = serializers.SerializerMethodField()
        expires_at = serializers.DateTimeField(read_only=True)
        expired = serializers.BooleanField(source="is_expired", read_only=True)

        class Meta(BaseModelSerializer.read.Meta):
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

        def get_link(self, obj):
            return obj.moderation_link if self.context.get("moderation") else None

    class write(serializers.Serializer):
        reason = serializers.ChoiceField(
            choices=Reason.choices,
            error_messages={"required": CHOOSE_REASON, "invalid_choice": CHOOSE_REASON},
        )


class SuspensionModelSerializer(BaseModelSerializer):
    class read(BaseModelSerializer.read):
        type = serializers.CharField(source="event_type", read_only=True)
        created_at = serializers.DateTimeField(source="starts_at", read_only=True)
        caused_at = serializers.DateTimeField(read_only=True)
        duration = serializers.CharField(source="duration_label", read_only=True)
        state = serializers.CharField(read_only=True)

        class Meta(BaseModelSerializer.read.Meta):
            model = Suspension
            fields = ["id", "type", "created_at", "caused_at", "ends_at", "duration", "state"]
