from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from commons.exceptions import BadRequest, Conflict, RetryLater
from commons.views import BaseViewSet
from swissfy.moderation.permissions import IsNotSuspended
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

    def pin_key(self):
        return get_object_or_404(ChatKey.objects.of(self.request.user), kind=ChatKey.Kind.PIN)

    @action(detail=False, methods=["post"], url_path="protection/unlock")
    def unlock(self, request):
        serializer = ChatKeyModelSerializer.unlock(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = self.pin_key()
        if key.unlock(serializer.validated_data["verifier"]):
            return Response(ChatKeyModelSerializer.sealed(key).data)
        if key.unlock_wait:
            raise RetryLater(_("Too many wrong attempts. Please try again later."), key.unlock_wait)
        raise PermissionDenied(_("Wrong PIN."))

    @action(detail=False, methods=["put"], url_path="protection/verifier")
    def verifier(self, request):
        serializer = ChatKeyModelSerializer.unlock(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = self.pin_key()
        if not key.needs_verifier:
            raise Conflict(_("The PIN is already secured."))
        key.set_verifier(serializer.validated_data["verifier"])
        key.save(update_fields=["pin_verifier"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"], url_path="keys")
    @transaction.atomic
    def add_device_key(self, request):
        if request.user.profile.chat_protection != Protection.DEVICE:
            raise BadRequest(_("Device keys only exist in the “Only on this device” mode."))
        serializer = ChatKeyModelSerializer.device(data=request.data)
        serializer.is_valid(raise_exception=True)
        if "replaces" in serializer.validated_data:
            request.user.chat_keys.filter(
                pk=serializer.validated_data["replaces"], kind=ChatKey.Kind.DEVICE
            ).update(active=False)
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
                "retention_days": settings.CHAT_RETENTION_DAYS,
            }
        )

    def page(self, conversation, after):
        return Response(
            {
                "messages": MessageModelSerializer.read(conversation.page(after), many=True).data,
                "statuses": conversation.statuses(),
                "chat_request": conversation.request_state,
                "can_request": conversation.can_request,
            }
        )

    @action(detail=True)
    def messages(self, request, username):
        query = MessageModelSerializer.query(data=request.query_params)
        query.is_valid(raise_exception=True)
        return self.page(self.get_conversation(), query.validated_data.get("after"))

    @action(detail=True, methods=["post"])
    def receive(self, request, username):
        receipt = MessageModelSerializer.receipt(data=request.data)
        receipt.is_valid(raise_exception=True)
        conversation = self.get_conversation()
        conversation.receive(receipt.validated_data["read"])
        return self.page(conversation, receipt.validated_data.get("after"))

    @messages.mapping.post
    @transaction.atomic
    def send(self, request, username):
        conversation = self.get_conversation()
        serializer = MessageModelSerializer.write(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not conversation.keys_match(serializer.validated_data):
            raise Conflict(_("The keys have changed."))
        lock_users(request.user, conversation.partner)
        if conversation.blocked_reason:
            raise PermissionDenied(conversation.blocked_reason)
        wait = Message.objects.slow_mode_wait(request.user, conversation.partner)
        if wait:
            raise RetryLater(_("Please wait a moment."), wait)
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
            raise Conflict(_("There already is a chat request."))
        if not conversation.can_request:
            raise PermissionDenied(_("This person does not accept chat requests."))
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
