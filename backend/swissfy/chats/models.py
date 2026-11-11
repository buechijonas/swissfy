import base64
import math
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Exists, OuterRef, Prefetch, Q, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from commons.models import BaseModel, BaseQuerySet, boolean

from .crypto import unwrap_message_key


def retention_cutoff():
    return timezone.now() - timedelta(days=settings.CHAT_RETENTION_DAYS)


def lock_users(*users):
    pks = [user.pk for user in users]
    list(get_user_model().objects.select_for_update().filter(pk__in=pks).order_by("pk"))


def annotate_chat_availability(members, viewer):
    chat_request = ChatRequest.objects.between(viewer, OuterRef("pk"))
    return members.annotate(has_chat_request=Exists(chat_request)).annotate(
        can_chat=boolean(
            ~Q(pk=viewer.pk) & (Q(has_chat_request=True) | Q(profile__chat_requests=True))
        )
    )


class ChatKeyQuerySet(BaseQuerySet):
    def active(self):
        return self.filter(active=True)

    def of(self, *users):
        return self.filter(user__in=users).active()


class ChatKey(BaseModel):
    class Kind(models.TextChoices):
        DEVICE = "device", "Gerät"
        PIN = "pin", "Chat-PIN"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_keys"
    )
    kind = models.CharField(max_length=10, choices=Kind.choices)
    public_key = models.JSONField()
    wrapped_private_key = models.TextField(blank=True)
    salt = models.CharField(max_length=64, blank=True)
    iv = models.CharField(max_length=32, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ChatKeyQuerySet.as_manager()

    def __str__(self):
        return f"ChatKey({self.user}, {self.kind}, {self.pk})"


class ChatRequestQuerySet(BaseQuerySet):
    def between(self, user, other):
        return self.filter(Q(sender=user, recipient=other) | Q(sender=other, recipient=user))

    def pending(self):
        return self.filter(status=ChatRequest.Status.PENDING)

    def started_by(self, user):
        Status = ChatRequest.Status
        return self.filter(Q(sender=user) | Q(recipient=user)).filter(
            Q(status=Status.ACCEPTED) | Q(status=Status.PENDING, sender=user)
        )

    def accepted_with(self, user, partner):
        return self.between(user, partner).filter(status=ChatRequest.Status.ACCEPTED)


class ChatRequest(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Offen"
        ACCEPTED = "accepted", "Angenommen"
        DECLINED = "declined", "Abgelehnt"

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_chat_requests"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_chat_requests"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ChatRequestQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["sender", "recipient"], name="unique_chat_request"),
        ]

    def __str__(self):
        return f"ChatRequest({self.sender} -> {self.recipient}, {self.status})"

    @property
    def is_accepted(self):
        return self.status == self.Status.ACCEPTED

    def partner_of(self, user):
        return self.recipient_id if self.sender_id == user.pk else self.sender_id

    def declined_by(self, user):
        return self.status == self.Status.DECLINED and self.recipient_id == user.pk

    def state_for(self, viewer):
        return {"status": self.status, "incoming": self.recipient_id == viewer.pk}

    def blocked_reason(self, sender):
        if self.is_accepted:
            return None
        if self.status == self.Status.DECLINED:
            return "Diese Chat-Anfrage wurde abgelehnt."
        if self.sender_id == sender.pk:
            return "Warte, bis deine Chat-Anfrage angenommen wurde."
        return "Nimm die Chat-Anfrage zuerst an."

    def resolve(self, status):
        self.status = status
        self.save(update_fields=["status"])
        return self


class MessageQuerySet(BaseQuerySet):
    def retained(self):
        return self.filter(created_at__gte=retention_cutoff())

    def between(self, user, partner):
        return self.filter(
            Q(sender=user, recipient=partner) | Q(sender=partner, recipient=user)
        ).retained()

    def for_reader(self, reader):
        envelopes = Envelope.objects.filter(key__user=reader)
        return self.select_related("sender").prefetch_related(
            Prefetch("envelopes", queryset=envelopes)
        )

    def mark_delivered(self):
        return self.filter(delivered_at__isnull=True).update(delivered_at=timezone.now())

    def mark_seen(self, with_receipt):
        now = Value(timezone.now())
        unread = Q(seen_at__isnull=True)
        marks = {"seen_at": Coalesce("seen_at", now)}
        if with_receipt:
            unread |= Q(read_at__isnull=True)
            marks["read_at"] = Coalesce("read_at", now)
        return self.filter(unread).update(**marks)

    def unread_partners(self, user):
        accepted = ChatRequest.objects.filter(
            Q(sender=OuterRef("sender"), recipient=user)
            | Q(sender=user, recipient=OuterRef("sender")),
            status=ChatRequest.Status.ACCEPTED,
        )
        archived = ArchivedChat.objects.filter(user=user, partner=OuterRef("sender"))
        return (
            self.filter(
                Exists(accepted),
                ~Exists(archived),
                recipient=user,
                sender__is_active=True,
                seen_at__isnull=True,
            )
            .retained()
            .order_by()
            .values_list("sender__username", flat=True)
            .distinct()
        )

    def slow_mode_wait(self, sender, recipient):
        last = self.filter(sender=sender, recipient=recipient).order_by("-id").first()
        if last is None:
            return 0
        elapsed = (timezone.now() - last.created_at).total_seconds()
        return max(0, math.ceil(settings.CHAT_SLOW_MODE_SECONDS - elapsed))


class Message(BaseModel):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_messages"
    )
    ciphertext = models.TextField()
    iv = models.CharField(max_length=32)
    server_key = models.BinaryField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    seen_at = models.DateTimeField(null=True, blank=True)

    objects = MessageQuerySet.as_manager()

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Message({self.sender} -> {self.recipient}, {self.pk})"

    @property
    def envelope_data(self):
        return [{"key": envelope.key_id, **envelope.data} for envelope in self.envelopes.all()]

    @property
    def message_key(self):
        if self.server_key is None:
            return None
        return base64.b64encode(unwrap_message_key(self)).decode()

    def status_for(self, show_read):
        if self.read_at and show_read:
            return "read"
        if self.delivered_at:
            return "delivered"
        return "sent"


class Envelope(BaseModel):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="envelopes")
    key = models.ForeignKey(ChatKey, on_delete=models.CASCADE, related_name="+")
    data = models.JSONField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["message", "key"], name="unique_envelope"),
        ]


class ArchivedChat(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="archived_chats"
    )
    partner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "partner"], name="unique_archived_chat"),
        ]

    def __str__(self):
        return f"ArchivedChat({self.user} -> {self.partner})"
