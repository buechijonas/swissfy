from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from commons.views import BaseViewSet
from swissfy.posts.permissions import IsNotSuspended
from swissfy.social.serializers import ProfileModelSerializer
from swissfy.social.users import with_viewer_relations

from .conversations import Conversation, ConversationList, protection_state, set_protection
from .models import ArchivedChat, ChatKey, ChatRequest, Message, lock_users
from .serializers import (
    ChatKeyModelSerializer,
    DeviceKeyInputSerializer,
    MessageInputSerializer,
    MessageModelSerializer,
    MessageQuerySerializer,
    Protection,
    ProtectionInputSerializer,
    ProtectionSerializer,
)

User = get_user_model()

NOT_SUSPENDED = [IsAuthenticated, IsNotSuspended]


def error(detail, status_code, **extra):
    return Response({"detail": detail, **extra}, status=status_code)


class ChatViewSet(BaseViewSet):
    def protection(self, request):
        return Response(ProtectionSerializer(protection_state(request.user)).data)

    @transaction.atomic
    def update_protection(self, request):
        serializer = ProtectionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_protection(
            request.user,
            serializer.validated_data["mode"],
            serializer.validated_data.get("key"),
        )
        return self.protection(request)

    def add_device_key(self, request):
        if request.user.profile.chat_protection != Protection.DEVICE:
            return error(
                "Gerät-Schlüssel gibt es nur im Modus „Nur auf diesem Gerät“.",
                status.HTTP_400_BAD_REQUEST,
            )
        serializer = DeviceKeyInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = ChatKey.objects.create(
            user=request.user,
            kind=ChatKey.Kind.DEVICE,
            public_key=serializer.validated_data["public_key"],
        )
        return Response(ChatKeyModelSerializer.read(key).data, status=status.HTTP_201_CREATED)

    def delivered(self, request):
        Message.objects.filter(recipient=request.user).mark_delivered()
        return Response({"unread": list(Message.objects.unread_partners(request.user))})

    def requests(self, request):
        users = User.objects.filter(
            is_active=True,
            sent_chat_requests__recipient=request.user,
            sent_chat_requests__status=ChatRequest.Status.PENDING,
        ).order_by("-sent_chat_requests__created_at")
        users = with_viewer_relations(users, request.user)
        context = self.get_serializer_context()
        return Response(ProfileModelSerializer.list(users, many=True, context=context).data)

    def conversations(self, request):
        return Response(ConversationList(request).results())


class ConversationViewSet(BaseViewSet):
    lookup_field = "username"
    permission_action_classes = {
        "send": NOT_SUSPENDED,
        "request_chat": NOT_SUSPENDED,
        "accept": NOT_SUSPENDED,
    }

    def get_queryset(self):
        return User.objects.exclude(pk=self.request.user.pk).filter(is_active=True)

    def get_conversation(self):
        return Conversation(self.request.user, self.get_object())

    def keys(self, request, username):
        conversation = self.get_conversation()
        return Response(
            {
                "keys": ChatKeyModelSerializer.read(conversation.keys, many=True).data,
                "server_key": conversation.needs_server_key,
            }
        )

    def messages(self, request, username):
        conversation = self.get_conversation()
        query = MessageQuerySerializer(data=request.query_params)
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

    @transaction.atomic
    def send(self, request, username):
        conversation = self.get_conversation()
        serializer = MessageInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not conversation.keys_match(serializer.validated_data):
            return error("Die Schlüssel haben sich geändert.", status.HTTP_409_CONFLICT)
        lock_users(request.user, conversation.partner)
        if conversation.blocked_reason:
            return error(conversation.blocked_reason, status.HTTP_403_FORBIDDEN)
        wait = Message.objects.slow_mode_wait(request.user, conversation.partner)
        if wait:
            response = error(
                "Bitte warte kurz.", status.HTTP_429_TOO_MANY_REQUESTS, retry_after=wait
            )
            response["Retry-After"] = str(wait)
            return response
        conversation.send(serializer.validated_data)
        return Response(
            {"retry_after": settings.CHAT_SLOW_MODE_SECONDS}, status=status.HTTP_201_CREATED
        )

    @transaction.atomic
    def request_chat(self, request, username):
        conversation = self.get_conversation()
        lock_users(request.user, conversation.partner)
        if conversation.has_open_request:
            return error("Es gibt bereits eine Chat-Anfrage.", status.HTTP_409_CONFLICT)
        if not conversation.can_request:
            return error("Diese Person nimmt keine Chat-Anfragen an.", status.HTTP_403_FORBIDDEN)
        ChatRequest.objects.between(request.user, conversation.partner).delete()
        chat_request = ChatRequest.objects.create(
            sender=request.user, recipient=conversation.partner
        )
        return Response(chat_request.state_for(request.user), status=status.HTTP_201_CREATED)

    def incoming_request(self):
        return get_object_or_404(
            ChatRequest.objects.pending(), sender=self.get_object(), recipient=self.request.user
        )

    def decline(self, request, username):
        chat_request = self.incoming_request().resolve(ChatRequest.Status.DECLINED)
        return Response(chat_request.state_for(request.user))

    def accept(self, request, username):
        chat_request = self.incoming_request().resolve(ChatRequest.Status.ACCEPTED)
        return Response(chat_request.state_for(request.user))

    @transaction.atomic
    def withdraw(self, request, username):
        partner = self.get_object()
        outgoing = ChatRequest.objects.pending().filter(sender=request.user, recipient=partner)
        get_object_or_404(outgoing).delete()
        Message.objects.filter(sender=request.user, recipient=partner).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def archive(self, request, username):
        ArchivedChat.objects.get_or_create(user=request.user, partner=self.get_object())
        return Response({"archived": True})

    def unarchive(self, request, username):
        ArchivedChat.objects.filter(user=request.user, partner=self.get_object()).delete()
        return Response({"archived": False})
