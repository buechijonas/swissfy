from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


def retention_cutoff():
    return timezone.now() - timedelta(days=settings.CHAT_RETENTION_DAYS)


class ChatKey(models.Model):
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

    def __str__(self):
        return f"ChatKey({self.user}, {self.kind}, {self.pk})"


class ChatRequest(models.Model):
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

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["sender", "recipient"], name="unique_chat_request"),
        ]

    @classmethod
    def between(cls, user, other):
        return cls.objects.filter(
            models.Q(sender=user, recipient=other) | models.Q(sender=other, recipient=user)
        ).first()

    def __str__(self):
        return f"ChatRequest({self.sender} -> {self.recipient}, {self.status})"


class Message(models.Model):
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

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Message({self.sender} -> {self.recipient}, {self.pk})"


class Envelope(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="envelopes")
    key = models.ForeignKey(ChatKey, on_delete=models.CASCADE, related_name="+")
    data = models.JSONField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["message", "key"], name="unique_envelope"),
        ]
