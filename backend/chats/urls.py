from django.urls import path

from . import views

urlpatterns = [
    path("protection/", views.ProtectionView.as_view(), name="chat-protection"),
    path("keys/", views.DeviceKeyView.as_view(), name="chat-device-keys"),
    path("delivered/", views.DeliveryView.as_view(), name="chat-delivered"),
    path("requests/", views.ChatRequestListView.as_view(), name="chat-requests"),
    path("conversations/", views.ConversationListView.as_view(), name="chat-conversations"),
    path("<str:username>/request/", views.ChatRequestView.as_view(), name="chat-request"),
    path(
        "<str:username>/request/withdraw/",
        views.ChatRequestWithdrawView.as_view(),
        name="chat-request-withdraw",
    ),
    path(
        "<str:username>/request/accept/",
        views.ChatRequestAcceptView.as_view(),
        name="chat-request-accept",
    ),
    path("<str:username>/archive/", views.ChatArchiveView.as_view(), name="chat-archive"),
    path("<str:username>/keys/", views.ConversationKeysView.as_view(), name="chat-keys"),
    path("<str:username>/messages/", views.MessagesView.as_view(), name="chat-messages"),
]
