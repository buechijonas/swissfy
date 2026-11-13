from functools import cached_property

from django.contrib.auth import get_user_model
from django.db.models import Exists, F, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce

from commons.models import boolean
from swissfy.accounts.models import UserProfile
from swissfy.social.models import Member

from .crypto import wrap_message_key
from .models import ArchivedChat, ChatKey, ChatRequest, Envelope, Message

User = get_user_model()
Protection = UserProfile.ChatProtection

PAGE_SIZE = 200


def needs_server_key(*users):
    return any(user.profile.chat_protection == Protection.STANDARD for user in users)


def protection_state(user):
    keys = ChatKey.objects.of(user)
    return {
        "mode": user.profile.chat_protection,
        "keys": keys,
        "pin_key": keys.filter(kind=ChatKey.Kind.PIN).first(),
    }


def set_protection(user, mode, key):
    user.chat_keys.update(active=False)
    if mode != Protection.STANDARD:
        ChatKey.objects.create(
            user=user,
            kind=ChatKey.Kind.PIN if mode == Protection.PIN else ChatKey.Kind.DEVICE,
            public_key=key["public_key"],
            wrapped_private_key=key.get("wrapped_private_key", ""),
            salt=key.get("salt", ""),
            iv=key.get("iv", ""),
        )
    user.profile.chat_protection = mode
    user.profile.save(update_fields=["chat_protection"])


class Conversation:
    def __init__(self, user, partner):
        self.user = user
        self.partner = partner

    @cached_property
    def chat_request(self):
        return ChatRequest.objects.between(self.user, self.partner).first()

    @property
    def accepted(self):
        return self.chat_request is None or self.chat_request.is_accepted

    @property
    def request_state(self):
        return self.chat_request and self.chat_request.state_for(self.user)

    @property
    def has_open_request(self):
        return bool(self.chat_request) and not self.chat_request.declined_by(self.user)

    @property
    def can_request(self):
        return not self.has_open_request and self.partner.profile.chat_requests

    @property
    def blocked_reason(self):
        if self.chat_request is None:
            return "Sende zuerst eine Chat-Anfrage."
        return self.chat_request.blocked_reason(self.user)

    @property
    def keys(self):
        return ChatKey.objects.of(self.user, self.partner)

    @property
    def needs_server_key(self):
        return needs_server_key(self.user, self.partner)

    @property
    def messages(self):
        return Message.objects.between(self.user, self.partner)

    def keys_match(self, data):
        expected = set(self.keys.values_list("pk", flat=True))
        envelope_keys = {envelope["key"] for envelope in data["envelopes"]}
        return envelope_keys == expected and ("message_key" in data) == self.needs_server_key

    def receive(self, read):
        incoming = Message.objects.filter(sender=self.partner, recipient=self.user)
        incoming.mark_delivered()
        if read:
            incoming.mark_seen(self.user.profile.read_receipts and self.accepted)

    def page(self, after):
        messages = self.messages.for_reader(self.user)
        if after is not None:
            return messages.filter(pk__gt=after)[:PAGE_SIZE]
        return reversed(messages.order_by("-id")[:PAGE_SIZE])

    def statuses(self):
        own = self.messages.filter(sender=self.user).with_status(self.user)
        own = own.order_by("-id")[:PAGE_SIZE]
        return {message.pk: message.status for message in own}

    def send(self, data):
        message = Message(
            sender=self.user, recipient=self.partner, ciphertext=data["ciphertext"], iv=data["iv"]
        )
        if "message_key" in data:
            message.server_key = wrap_message_key(message, data["message_key"])
        message.save()
        Envelope.objects.bulk_create(
            Envelope(message=message, key_id=envelope.pop("key"), data=envelope)
            for envelope in data["envelopes"]
        )
        return message


def conversation_partners(user):
    partner = OuterRef("pk")
    chat_requests = ChatRequest.objects.started_by(user).between(user, partner)
    last_message = Message.objects.between(user, partner).order_by("-id")
    started_at = Subquery(chat_requests.values("created_at")[:1])
    return (
        Member.objects.filter(Exists(chat_requests), is_active=True)
        .with_viewer_relations(user)
        .annotate(
            last_message_id=Subquery(last_message.values("id")[:1]),
            last_sender_id=Subquery(last_message.values("sender")[:1]),
            last_seen_at=Subquery(last_message.values("seen_at")[:1]),
            activity=Coalesce(Subquery(last_message.values("created_at")[:1]), started_at),
            archived=Exists(ArchivedChat.objects.filter(user=user, partner=partner)),
            pending=Exists(ChatRequest.objects.pending().filter(sender=user, recipient=partner)),
        )
        .annotate(unread=boolean(Q(last_sender_id=F("pk"), last_seen_at__isnull=True)))
        .order_by("-activity")
    )


def last_messages(user, partners):
    ids = [partner.last_message_id for partner in partners if partner.last_message_id]
    return Message.objects.filter(pk__in=ids).for_reader(user).in_bulk()
