from django.utils import timezone
from rest_framework import serializers

from moderation.sanctions import SUSPENSION_STEPS
from posts.serializers import AuthorSerializer
from social.models import FriendRequest, Friendship

from .models import Notification

Kind = Notification.Kind
PREVIEW_LENGTH = 80


def local_date(value):
    return timezone.localtime(value).strftime("%d.%m.%Y")


def quote(text):
    text = " ".join(text.split())
    return f"«{text[:PREVIEW_LENGTH]}…»" if len(text) > PREVIEW_LENGTH else f"«{text}»"


class NotificationSerializer(serializers.ModelSerializer):
    actor = AuthorSerializer(read_only=True)
    message = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()
    read = serializers.SerializerMethodField()
    friend_request = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ["id", "kind", "actor", "message", "link", "created_at", "read", "friend_request"]

    def get_read(self, obj):
        return obj.read_at is not None

    def get_message(self, obj):
        name = f"@{obj.actor.username}" if obj.actor else ""
        match obj.kind:
            case Kind.WARNING:
                return f"Du wurdest verwarnt: {obj.warning.get_reason_display()}."
            case Kind.WARNING_EXPIRED:
                reason = obj.warning.get_reason_display()
                return (
                    f"Deine Verwarnung «{reason}» vom "
                    f"{local_date(obj.warning.created_at)} ist verjährt."
                )
            case Kind.SUSPENSION:
                return self.suspension_message(obj.suspension)
            case Kind.COMMENT:
                return f"{name} hat deinen Feed kommentiert: {quote(obj.comment.text)}"
            case Kind.LIKE:
                return f"{name} gefällt dein Feed."
            case Kind.FOLLOW:
                return f"{name} folgt dir jetzt."
            case Kind.FRIEND_REQUEST:
                return f"{name} möchte mit dir befreundet sein."
        return ""

    def suspension_message(self, suspension):
        duration = SUSPENSION_STEPS[suspension.step][1]
        if suspension.ends_at is None:
            return "Dein Konto wurde dauerhaft gesperrt."
        until = local_date(suspension.ends_at)
        if suspension.starts_at > timezone.now():
            start = local_date(suspension.starts_at)
            return f"Dein Konto wird für {duration} gesperrt, ab {start} bis {until}."
        return f"Dein Konto wurde für {duration} gesperrt, bis {until}."

    def get_link(self, obj):
        match obj.kind:
            case Kind.WARNING | Kind.WARNING_EXPIRED | Kind.SUSPENSION:
                return f"/profile/{obj.recipient.username}?tab=status"
            case Kind.COMMENT:
                return f"/comments/{obj.comment.uuid}"
            case Kind.LIKE:
                return f"/posts/{obj.post.uuid}"
        return f"/profile/{obj.actor.username}" if obj.actor else None

    def get_friend_request(self, obj):
        if obj.kind != Kind.FRIEND_REQUEST:
            return None
        if obj.resolution:
            return obj.resolution
        if FriendRequest.objects.filter(sender=obj.actor, receiver=obj.recipient).exists():
            return "pending"
        if Friendship.objects.filter(user=obj.recipient, friend=obj.actor).exists():
            return Notification.Resolution.ACCEPTED
        return Notification.Resolution.DECLINED
