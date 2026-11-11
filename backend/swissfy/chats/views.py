from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from commons.exceptions import BadRequest, Conflict, RetryLater
from commons.views import BaseViewSet
from swissfy.posts.permissions import IsNotSuspended
from swissfy.social.models import Member
from swissfy.social.serializers import ProfileModelSerializer

from .conversations import (
    Conversation,
    conversation_partners,
    last_messages,
    protection_state,
    set_protection,
)
from .models import ArchivedChat, ChatKey, ChatRequest, Message, lock_users
from .serializers import (
    ChatKeyModelSerializer,
    ConversationSerializer,
    MessageModelSerializer,
    Protection,
    ProtectionSerializer,
)

User = get_user_model()

NOT_SUSPENDED = [IsAuthenticated, IsNotSuspended]


class ChatViewSet(BaseViewSet):
    @action(detail=False)
    def protection(self, request):
        return Response(ProtectionSerializer.read(protection_state(request.user)).data)

    @protection.mapping.put
    @transaction.atomic
    def update_protection(self, request):
        serializer = ProtectionSerializer.write(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_protection(
            request.user,
            serializer.validated_data["mode"],
            serializer.validated_data.get("key"),
        )
        return self.protection(request)

    @action(detail=False, methods=["post"], url_path="keys")
    def add_device_key(self, request):
        if request.user.profile.chat_protection != Protection.DEVICE:
            raise BadRequest("Gerät-Schlüssel gibt es nur im Modus „Nur auf diesem Gerät“.")
        serializer = ChatKeyModelSerializer.device(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = ChatKey.objects.create(
            user=request.user,
            kind=ChatKey.Kind.DEVICE,
            public_key=serializer.validated_data["public_key"],
        )
        return Response(ChatKeyModelSerializer.read(key).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def delivered(self, request):
        Message.objects.filter(recipient=request.user).mark_delivered()
        return Response({"unread": list(Message.objects.unread_partners(request.user))})

    @action(detail=False)
    def requests(self, request):
        users = (
            Member.objects.filter(
                is_active=True,
                sent_chat_requests__recipient=request.user,
                sent_chat_requests__status=ChatRequest.Status.PENDING,
            )
            .with_viewer_relations(request.user)
            .order_by("-sent_chat_requests__created_at")
        )
        context = self.get_serializer_context()
        return Response(ProfileModelSerializer.list(users, many=True, context=context).data)

    @action(detail=False)
    def conversations(self, request):
        partners = list(conversation_partners(request.user))
        context = {
            **self.get_serializer_context(),
            "messages": last_messages(request.user, partners),
        }
        return Response(ConversationSerializer(partners, many=True, context=context).data)


class ConversationViewSet(BaseViewSet):
    lookup_field = "username"
    permission_action_classes = {"send": NOT_SUSPENDED, "request_chat": NOT_SUSPENDED}

    def get_queryset(self):
        return User.objects.exclude(pk=self.request.user.pk).filter(is_active=True)

    def get_conversation(self):
        return Conversation(self.request.user, self.get_object())

    @action(detail=True)
    def keys(self, request, username):
        conversation = self.get_conversation()
        return Response(
            {
                "keys": ChatKeyModelSerializer.read(conversation.keys, many=True).data,
                "server_key": conversation.needs_server_key,
            }
        )

    @action(detail=True)
    def messages(self, request, username):
        conversation = self.get_conversation()
        query = MessageModelSerializer.query(data=request.query_params)
        query.is_valid(raise_exception=True)
        conversation.receive(query.validated_data["read"])
        page = conversation.page(query.validated_data.get("after"))
        context = {"viewer": request.user, "show_read": conversation.show_read}
        return Response(
            {
                "messages": MessageModelSerializer.read(page, many=True, context=context).data,
                "statuses": conversation.statuses(),
                "chat_request": conversation.request_state,
                "can_request": conversation.can_request,
            }
        )

    @messages.mapping.post
    @transaction.atomic
    def send(self, request, username):
        conversation = self.get_conversation()
        serializer = MessageModelSerializer.write(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not conversation.keys_match(serializer.validated_data):
            raise Conflict("Die Schlüssel haben sich geändert.")
        lock_users(request.user, conversation.partner)
        if conversation.blocked_reason:
            raise PermissionDenied(conversation.blocked_reason)
        wait = Message.objects.slow_mode_wait(request.user, conversation.partner)
        if wait:
            raise RetryLater("Bitte warte kurz.", wait)
        conversation.send(serializer.validated_data)
        return Response(
            {"retry_after": settings.CHAT_SLOW_MODE_SECONDS}, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"], url_path="request")
    @transaction.atomic
    def request_chat(self, request, username):
        conversation = self.get_conversation()
        lock_users(request.user, conversation.partner)
        if conversation.has_open_request:
            raise Conflict("Es gibt bereits eine Chat-Anfrage.")
        if not conversation.can_request:
            raise PermissionDenied("Diese Person nimmt keine Chat-Anfragen an.")
        ChatRequest.objects.between(request.user, conversation.partner).delete()
        chat_request = ChatRequest.objects.create(
            sender=request.user, recipient=conversation.partner
        )
        return Response(chat_request.state_for(request.user), status=status.HTTP_201_CREATED)

    def incoming_request(self):
        return get_object_or_404(
            ChatRequest.objects.pending(), sender=self.get_object(), recipient=self.request.user
        )

    @request_chat.mapping.delete
    def decline(self, request, username):
        chat_request = self.incoming_request().resolve(ChatRequest.Status.DECLINED)
        return Response(chat_request.state_for(request.user))

    @action(
        detail=True, methods=["post"], url_path="request/accept", permission_classes=NOT_SUSPENDED
    )
    def accept(self, request, username):
        chat_request = self.incoming_request().resolve(ChatRequest.Status.ACCEPTED)
        return Response(chat_request.state_for(request.user))

    @action(detail=True, methods=["post"], url_path="request/withdraw")
    @transaction.atomic
    def withdraw(self, request, username):
        partner = self.get_object()
        outgoing = ChatRequest.objects.pending().filter(sender=request.user, recipient=partner)
        get_object_or_404(outgoing).delete()
        Message.objects.filter(sender=request.user, recipient=partner).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def archive(self, request, username):
        ArchivedChat.objects.get_or_create(user=request.user, partner=self.get_object())
        return Response({"archived": True})

    @archive.mapping.delete
    def unarchive(self, request, username):
        ArchivedChat.objects.filter(user=request.user, partner=self.get_object()).delete()
        return Response({"archived": False})
