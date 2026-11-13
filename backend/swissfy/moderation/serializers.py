from rest_framework import serializers

from commons.fields import ConstantField
from commons.serializers import BaseModelSerializer
from swissfy.posts.serializers import CommentModelSerializer, PostModelSerializer

from .models import Reason, Report, Suspension, Warning
from .reviews import ReportedContent

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
        past = serializers.BooleanField(source="is_past", read_only=True)

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
                "past",
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
        past = serializers.BooleanField(source="is_past", read_only=True)
        status_text = serializers.CharField(read_only=True)

        class Meta(BaseModelSerializer.read.Meta):
            model = Suspension
            fields = [
                "id",
                "type",
                "created_at",
                "caused_at",
                "ends_at",
                "duration",
                "state",
                "past",
                "status_text",
            ]


class ReportGroupSerializer:
    class post(serializers.Serializer):
        type = serializers.CharField(source="kind", read_only=True)
        report_count = serializers.IntegerField(read_only=True)
        warned = serializers.BooleanField(read_only=True)
        post = PostModelSerializer.read(read_only=True)

    class comment(serializers.Serializer):
        type = serializers.CharField(source="kind", read_only=True)
        report_count = serializers.IntegerField(read_only=True)
        warned = serializers.BooleanField(read_only=True)
        comment = CommentModelSerializer.read(read_only=True)
        post = PostModelSerializer.summary(source="summary", read_only=True)

    @classmethod
    def of(cls, group):
        return cls.post if group.post else cls.comment


class ModerationDetailsSerializer(serializers.Serializer):
    report_count = serializers.IntegerField(source="open_report_count", read_only=True)
    can_warn = serializers.BooleanField(read_only=True)
    reasons = ConstantField(Reason.options())
    warnings = WarningModelSerializer.read(source="warning_set", many=True, read_only=True)


class ReportedContentSerializer(serializers.Serializer):
    type = serializers.CharField(source="kind", read_only=True)
    text = serializers.CharField(read_only=True)
    report_count = serializers.IntegerField(read_only=True)
    open_count = serializers.IntegerField(read_only=True)
    link = serializers.CharField(read_only=True)


class ModerationStatusSerializer(serializers.Serializer):
    events = serializers.SerializerMethodField()
    reports = serializers.SerializerMethodField()

    @property
    def moderating(self):
        return self.context["moderation"]

    def get_events(self, user):
        warnings = Warning.objects.filter(user=user).select_related("post", "comment")
        suspensions = Suspension.objects.filter(user=user).select_related("warning")
        context = {"moderation": self.moderating}
        events = [
            *WarningModelSerializer.read(warnings, many=True, context=context).data,
            *SuspensionModelSerializer.read(suspensions, many=True).data,
        ]
        return sorted(
            events,
            key=lambda event: (event["caused_at"], event["type"] == "suspension"),
            reverse=True,
        )

    def get_reports(self, user):
        if not self.moderating:
            return None
        reported = [ReportedContent(group) for group in Report.objects.about(user)]
        return ReportedContentSerializer(reported, many=True).data
