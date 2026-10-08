import math

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Exists, OuterRef, Prefetch, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import get_or_create_profile
from social.serializers import ProfileListSerializer
from social.views import with_viewer_relations

from .crypto import wrap_message_key
from .models import ChatKey, ChatRequest, Envelope, Message, retention_cutoff
from .serializers import (
    ChatKeySerializer,
    DeviceKeyInputSerializer,
    MessageInputSerializer,
    MessageQuerySerializer,
    MessageSerializer,
    PinKeySerializer,
    Protection,
    ProtectionInputSerializer,
    message_status,
)

User = get_user_model()

PAGE_SIZE = 200


def protection_of(user):
    return get_or_create_profile(user).chat_protection


def needs_server_key(*users):
    return any(protection_of(user) == Protection.STANDARD for user in users)


def slow_mode_wait(sender, recipient):
    last = Message.objects.filter(sender=sender, recipient=recipient).order_by("-id").first()
    if last is None:
        return 0
    remaining = settings.CHAT_SLOW_MODE_SECONDS - (timezone.now() - last.created_at).total_seconds()
    return max(0, math.ceil(remaining))


def request_state(chat_request, viewer):
    if chat_request is None:
        return None
    return {"status": chat_request.status, "incoming": chat_request.recipient_id == viewer.pk}


def declined_by(chat_request, user):
    return (
        chat_request.status == ChatRequest.Status.DECLINED and chat_request.recipient_id == user.pk
    )


def can_request(chat_request, sender, recipient):
    if chat_request and not declined_by(chat_request, sender):
        return False
    return get_or_create_profile(recipient).chat_requests


def send_blocked_reason(chat_request, sender):
    if chat_request is None:
        return "Sende zuerst eine Chat-Anfrage."
    if chat_request.status == ChatRequest.Status.ACCEPTED:
        return None
    if chat_request.status == ChatRequest.Status.DECLINED:
        return "Diese Chat-Anfrage wurde abgelehnt."
    if chat_request.sender_id == sender.pk:
        return "Warte, bis deine Chat-Anfrage angenommen wurde."
    return "Nimm die Chat-Anfrage zuerst an."


def lock_users(*users):
    list(User.objects.select_for_update().filter(pk__in=[u.pk for u in users]).order_by("pk"))


def active_keys(*users):
    return ChatKey.objects.filter(user__in=users, active=True)


class ProtectionView(APIView):
    def protection_response(self, user):
        keys = active_keys(user)
        pin_key = keys.filter(kind=ChatKey.Kind.PIN).first()
        return Response(
            {
                "mode": protection_of(user),
                "keys": ChatKeySerializer(keys, many=True).data,
                "pin_key": PinKeySerializer(pin_key).data if pin_key else None,
            }
        )

    def get(self, request):
        return self.protection_response(request.user)

    @transaction.atomic
    def put(self, request):
        serializer = ProtectionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mode = serializer.validated_data["mode"]
        request.user.chat_keys.update(active=False)
        if mode != Protection.STANDARD:
            key = serializer.validated_data["key"]
            ChatKey.objects.create(
                user=request.user,
                kind=ChatKey.Kind.PIN if mode == Protection.PIN else ChatKey.Kind.DEVICE,
                public_key=key["public_key"],
                wrapped_private_key=key.get("wrapped_private_key", ""),
                salt=key.get("salt", ""),
                iv=key.get("iv", ""),
            )
        profile = get_or_create_profile(request.user)
        profile.chat_protection = mode
        profile.save(update_fields=["chat_protection"])
        return self.protection_response(request.user)


class DeviceKeyView(APIView):
    def post(self, request):
        if protection_of(request.user) != Protection.DEVICE:
            return Response(
                {"detail": "Gerät-Schlüssel gibt es nur im Modus „Nur auf diesem Gerät“."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = DeviceKeyInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = ChatKey.objects.create(
            user=request.user,
            kind=ChatKey.Kind.DEVICE,
            public_key=serializer.validated_data["public_key"],
        )
        return Response(ChatKeySerializer(key).data, status=status.HTTP_201_CREATED)


class ConversationView(APIView):
    def get_partner(self, request, username):
        return get_object_or_404(
            User.objects.exclude(pk=request.user.pk), username=username, is_active=True
        )


class ConversationKeysView(ConversationView):
    def get(self, request, username):
        partner = self.get_partner(request, username)
        return Response(
            {
                "keys": ChatKeySerializer(active_keys(request.user, partner), many=True).data,
                "server_key": needs_server_key(request.user, partner),
            }
        )


class MessagesView(ConversationView):
    def get(self, request, username):
        partner = self.get_partner(request, username)
        query = MessageQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        my_receipts = get_or_create_profile(request.user).read_receipts
        chat_request = ChatRequest.between(request.user, partner)
        accepted = chat_request is None or chat_request.status == ChatRequest.Status.ACCEPTED

        incoming = Message.objects.filter(sender=partner, recipient=request.user)
        incoming.filter(delivered_at__isnull=True).update(delivered_at=timezone.now())
        if query.validated_data["read"]:
            now = Value(timezone.now())
            unread = Q(seen_at__isnull=True)
            marks = {"seen_at": Coalesce("seen_at", now)}
            if my_receipts and accepted:
                unread |= Q(read_at__isnull=True)
                marks["read_at"] = Coalesce("read_at", now)
            incoming.filter(unread).update(**marks)

        conversation = Message.objects.filter(
            Q(sender=request.user, recipient=partner) | Q(sender=partner, recipient=request.user),
            created_at__gte=retention_cutoff(),
        )
        messages = conversation.select_related("sender").prefetch_related(
            Prefetch("envelopes", queryset=Envelope.objects.filter(key__user=request.user))
        )
        after = query.validated_data.get("after")
        if after is not None:
            messages = messages.filter(pk__gt=after)[:PAGE_SIZE]
        else:
            messages = reversed(messages.order_by("-id")[:PAGE_SIZE])

        show_read = my_receipts and get_or_create_profile(partner).read_receipts
        own = conversation.filter(sender=request.user).order_by("-id")[:PAGE_SIZE]
        context = {"viewer": request.user, "show_read": show_read}
        return Response(
            {
                "messages": MessageSerializer(messages, many=True, context=context).data,
                "statuses": {message.pk: message_status(message, show_read) for message in own},
                "chat_request": request_state(chat_request, request.user),
                "can_request": can_request(chat_request, request.user, partner),
            }
        )

    @transaction.atomic
    def post(self, request, username):
        partner = self.get_partner(request, username)
        serializer = MessageInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        expected_keys = set(active_keys(request.user, partner).values_list("pk", flat=True))
        if {envelope["key"] for envelope in data["envelopes"]} != expected_keys or (
            "message_key" in data
        ) != needs_server_key(request.user, partner):
            return Response(
                {"detail": "Die Schlüssel haben sich geändert."}, status=status.HTTP_409_CONFLICT
            )

        lock_users(request.user, partner)
        chat_request = ChatRequest.between(request.user, partner)
        blocked = send_blocked_reason(chat_request, request.user)
        if blocked:
            return Response({"detail": blocked}, status=status.HTTP_403_FORBIDDEN)

        wait = slow_mode_wait(request.user, partner)
        if wait:
            return Response(
                {"detail": "Bitte warte kurz.", "retry_after": wait},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": str(wait)},
            )

        message = Message(
            sender=request.user, recipient=partner, ciphertext=data["ciphertext"], iv=data["iv"]
        )
        if "message_key" in data:
            message.server_key = wrap_message_key(message, data["message_key"])
        message.save()
        Envelope.objects.bulk_create(
            Envelope(
                message=message,
                key_id=envelope.pop("key"),
                data=envelope,
            )
            for envelope in data["envelopes"]
        )
        return Response(
            {"retry_after": settings.CHAT_SLOW_MODE_SECONDS}, status=status.HTTP_201_CREATED
        )


def unread_partners(user):
    accepted = ChatRequest.objects.filter(
        Q(sender=OuterRef("sender"), recipient=user) | Q(sender=user, recipient=OuterRef("sender")),
        status=ChatRequest.Status.ACCEPTED,
    )
    return (
        Message.objects.filter(
            Exists(accepted),
            recipient=user,
            sender__is_active=True,
            seen_at__isnull=True,
            created_at__gte=retention_cutoff(),
        )
        .order_by()
        .values_list("sender__username", flat=True)
        .distinct()
    )


class DeliveryView(APIView):
    def post(self, request):
        Message.objects.filter(recipient=request.user, delivered_at__isnull=True).update(
            delivered_at=timezone.now()
        )
        return Response({"unread": list(unread_partners(request.user))})


class ChatRequestView(ConversationView):
    @transaction.atomic
    def post(self, request, username):
        partner = self.get_partner(request, username)
        lock_users(request.user, partner)
        existing = ChatRequest.between(request.user, partner)
        if existing and not declined_by(existing, request.user):
            return Response(
                {"detail": "Es gibt bereits eine Chat-Anfrage."}, status=status.HTTP_409_CONFLICT
            )
        if not can_request(existing, request.user, partner):
            return Response(
                {"detail": "Diese Person nimmt keine Chat-Anfragen an."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if existing:
            existing.delete()
        chat_request = ChatRequest.objects.create(sender=request.user, recipient=partner)
        return Response(request_state(chat_request, request.user), status=status.HTTP_201_CREATED)

    def delete(self, request, username):
        chat_request = self.incoming_request(request, username)
        chat_request.status = ChatRequest.Status.DECLINED
        chat_request.save(update_fields=["status"])
        return Response(request_state(chat_request, request.user))

    def incoming_request(self, request, username):
        return get_object_or_404(
            ChatRequest,
            sender=self.get_partner(request, username),
            recipient=request.user,
            status=ChatRequest.Status.PENDING,
        )


class ChatRequestWithdrawView(ConversationView):
    @transaction.atomic
    def post(self, request, username):
        partner = self.get_partner(request, username)
        chat_request = get_object_or_404(
            ChatRequest, sender=request.user, recipient=partner, status=ChatRequest.Status.PENDING
        )
        chat_request.delete()
        Message.objects.filter(sender=request.user, recipient=partner).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChatRequestAcceptView(ChatRequestView):
    def post(self, request, username):
        chat_request = self.incoming_request(request, username)
        chat_request.status = ChatRequest.Status.ACCEPTED
        chat_request.save(update_fields=["status"])
        return Response(request_state(chat_request, request.user))


class ChatRequestListView(generics.ListAPIView):
    serializer_class = ProfileListSerializer
    pagination_class = None

    def get_queryset(self):
        viewer = self.request.user
        users = User.objects.filter(
            is_active=True,
            sent_chat_requests__recipient=viewer,
            sent_chat_requests__status=ChatRequest.Status.PENDING,
        ).order_by("-sent_chat_requests__created_at")
        return with_viewer_relations(users, viewer)


class ConversationListView(APIView):
    def get(self, request):
        me = request.user
        chat_requests = ChatRequest.objects.filter(Q(sender=me) | Q(recipient=me)).filter(
            Q(status=ChatRequest.Status.ACCEPTED) | Q(status=ChatRequest.Status.PENDING, sender=me)
        )
        started = {
            (r.recipient_id if r.sender_id == me.pk else r.sender_id): r.created_at
            for r in chat_requests
        }
        last_message = Message.objects.filter(
            Q(sender=me, recipient=OuterRef("pk")) | Q(sender=OuterRef("pk"), recipient=me),
            created_at__gte=retention_cutoff(),
        ).order_by("-id")
        users = with_viewer_relations(
            User.objects.filter(pk__in=started, is_active=True), me
        ).annotate(last_message_id=Subquery(last_message.values("id")[:1]))
        messages = Message.objects.filter(
            pk__in=[user.last_message_id for user in users if user.last_message_id]
        ).prefetch_related(Prefetch("envelopes", queryset=Envelope.objects.filter(key__user=me)))
        messages = {message.pk: message for message in messages.select_related("sender")}

        my_receipts = get_or_create_profile(me).read_receipts
        conversations = []
        for user in users:
            message = messages.get(user.last_message_id)
            context = {
                "viewer": me,
                "show_read": my_receipts and get_or_create_profile(user).read_receipts,
            }
            conversations.append(
                {
                    **ProfileListSerializer(user).data,
                    "last_message": message and MessageSerializer(message, context=context).data,
                    "unread": bool(message and message.sender_id != me.pk and not message.seen_at),
                    "activity": message.created_at if message else started[user.pk],
                }
            )
        conversations.sort(key=lambda conversation: conversation["activity"], reverse=True)
        for conversation in conversations:
            del conversation["activity"]
        return Response(conversations)
