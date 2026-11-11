from functools import cached_property

from django.contrib.auth import get_user_model
from django.db.models import OuterRef, Subquery

from swissfy.accounts.models import UserProfile
from swissfy.social.serializers import ProfileModelSerializer
from swissfy.social.users import with_viewer_relations

from .crypto import wrap_message_key
from .models import ChatKey, ChatRequest, Envelope, Message
from .serializers import MessageModelSerializer

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
    def show_read(self):
        return self.user.profile.read_receipts and self.partner.profile.read_receipts

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
        own = self.messages.filter(sender=self.user).order_by("-id")[:PAGE_SIZE]
        return {message.pk: message.status_for(self.show_read) for message in own}

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


class ConversationList:
    def __init__(self, request):
        self.request = request
        self.me = request.user
        chat_requests = list(ChatRequest.objects.started_by(self.me))
        self.started = {chat.partner_of(self.me): chat.created_at for chat in chat_requests}
        self.pending = {chat.recipient_id for chat in chat_requests if not chat.is_accepted}
        self.archived = set(self.me.archived_chats.values_list("partner_id", flat=True))
        self.partners = list(self.load_partners())
        self.last_messages = self.load_last_messages()

    def load_partners(self):
        last_message = Message.objects.between(self.me, OuterRef("pk")).order_by("-id")
        users = User.objects.filter(pk__in=self.started, is_active=True)
        return with_viewer_relations(users, self.me).annotate(
            last_message_id=Subquery(last_message.values("id")[:1])
        )

    def load_last_messages(self):
        ids = [partner.last_message_id for partner in self.partners if partner.last_message_id]
        return Message.objects.filter(pk__in=ids).for_reader(self.me).in_bulk()

    def results(self):
        entries = sorted(
            (self.entry(partner) for partner in self.partners),
            key=lambda entry: entry[0],
            reverse=True,
        )
        return [data for _, data in entries]

    def entry(self, partner):
        message = self.last_messages.get(partner.last_message_id)
        show_read = self.me.profile.read_receipts and partner.profile.read_receipts
        context = {"viewer": self.me, "show_read": show_read}
        data = {
            **ProfileModelSerializer.list(partner, context={"request": self.request}).data,
            "last_message": message and MessageModelSerializer.read(message, context=context).data,
            "unread": bool(message and message.sender_id != self.me.pk and not message.seen_at),
            "archived": partner.pk in self.archived,
            "pending": partner.pk in self.pending,
        }
        return (message.created_at if message else self.started[partner.pk]), data
