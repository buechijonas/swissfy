from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from commons.fields import CompactNumberField
from commons.serializers import BaseModelSerializer, UUIDModelSerializer

from ..models import Comment, CommentVote
from .common import AuthorModelSerializer, ModeratedSerializerMixin, UnavailableSerializer


class CommentModelSerializer(UUIDModelSerializer):
    class read(ModeratedSerializerMixin, UUIDModelSerializer.read):
        post_id = serializers.UUIDField(source="post.uuid", read_only=True)
        parent_id = serializers.UUIDField(source="parent_uuid", read_only=True)
        author = AuthorModelSerializer.read(read_only=True)
        reply_to = serializers.CharField(read_only=True)
        is_post_author = serializers.BooleanField(read_only=True)
        reply_count = serializers.IntegerField(read_only=True)
        score = CompactNumberField()
        my_vote = serializers.IntegerField(read_only=True)
        latest_reply = serializers.SerializerMethodField()
        can_delete = serializers.BooleanField(source="is_own", read_only=True)
        can_vote = serializers.BooleanField(read_only=True)
        moderated_actions = ["can_report", "can_delete", "can_vote"]

        class Meta(UUIDModelSerializer.read.Meta):
            model = Comment
            fields = UUIDModelSerializer.read.Meta.fields + [
                "post_id",
                "parent_id",
                "author",
                "text",
                "created_at",
                "reply_to",
                "is_post_author",
                "reply_count",
                "score",
                "my_vote",
                "latest_reply",
                "can_delete",
                "can_vote",
                "hidden",
                "reported",
                "can_report",
            ]

        def get_latest_reply(self, obj):
            if obj.latest_reply is None:
                return None
            return CommentModelSerializer.read(obj.latest_reply, context=self.context).data

    class unavailable(UnavailableSerializer):
        blocked = _("This comment has been blocked.")
        hidden = _("This comment is not visible.")

        class Meta(UnavailableSerializer.Meta):
            model = Comment

    class write(BaseModelSerializer.write):
        class Meta(BaseModelSerializer.write.Meta):
            model = Comment
            fields = ["text"]

    class vote(serializers.Serializer):
        value = serializers.JSONField()

        def validate_value(self, value):
            if value not in (*CommentVote.Value.values, 0):
                raise serializers.ValidationError(_("Invalid vote."))
            return value
