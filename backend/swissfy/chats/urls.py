from django.urls import path

from .views import ChatViewSet, ConversationViewSet

urlpatterns = [
    path(
        "protection/",
        ChatViewSet.as_view({"get": "protection", "put": "update_protection"}),
        name="chat-protection",
    ),
    path("keys/", ChatViewSet.as_view({"post": "add_device_key"}), name="chat-device-keys"),
    path("delivered/", ChatViewSet.as_view({"post": "delivered"}), name="chat-delivered"),
    path("requests/", ChatViewSet.as_view({"get": "requests"}), name="chat-requests"),
    path(
        "conversations/",
        ChatViewSet.as_view({"get": "conversations"}),
        name="chat-conversations",
    ),
    path(
        "<str:username>/request/",
        ConversationViewSet.as_view({"post": "request_chat", "delete": "decline"}),
        name="chat-request",
    ),
    path(
        "<str:username>/request/withdraw/",
        ConversationViewSet.as_view({"post": "withdraw"}),
        name="chat-request-withdraw",
    ),
    path(
        "<str:username>/request/accept/",
        ConversationViewSet.as_view({"post": "accept"}),
        name="chat-request-accept",
    ),
    path(
        "<str:username>/archive/",
        ConversationViewSet.as_view({"post": "archive", "delete": "unarchive"}),
        name="chat-archive",
    ),
    path(
        "<str:username>/keys/",
        ConversationViewSet.as_view({"get": "keys"}),
        name="chat-keys",
    ),
    path(
        "<str:username>/messages/",
        ConversationViewSet.as_view({"get": "messages", "post": "send"}),
        name="chat-messages",
    ),
]
