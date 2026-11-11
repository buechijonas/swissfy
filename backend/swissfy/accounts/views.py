from django.contrib import auth
from django.http import Http404
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from commons.views import BaseViewSet

from . import devices
from .consent import push_to_govex
from .models import UserConsent, user_consent
from .serializers import ConsentModelSerializer, DeviceTokenModelSerializer, UserModelSerializer


class AuthViewSet(BaseViewSet):

    def user_data(self, user):
        return UserModelSerializer.read(user, context=self.get_serializer_context()).data

    def device_token(self):
        serializer = DeviceTokenModelSerializer.write(data=self.request.data)
        return serializer.validated_data.get("token") if serializer.is_valid() else None

    @action(detail=False, permission_classes=[AllowAny])
    def me(self, request):
        get_token(request)
        if request.user.is_anonymous:
            return Response({"user": None})
        return Response({"user": self.user_data(request.user)})

    @action(detail=False, methods=["post"])
    def logout(self, request):
        devices.forget_device(request)
        auth.logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"], url_path="device")
    def sync_device(self, request):
        return Response({"token": devices.keep_or_issue(request, self.device_token())})

    @sync_device.mapping.delete
    def forget_device(self, request):
        devices.forget_device(request)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=["post"], url_path="device/restore", permission_classes=[AllowAny]
    )
    def restore_device(self, request):
        device = devices.find_device(self.device_token())
        if device is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        auth.login(request, device.user)
        devices.remember_device(request, device)
        get_token(request)
        return Response({"user": self.user_data(device.user)})

    @action(detail=False, methods=["post"], url_path="consent/<str:field>")
    def accept_consent(self, request, field):
        if field not in UserConsent.FIELDS:
            raise Http404
        consent = user_consent(request.user)
        consent.accept(field)
        push_to_govex(request.user.profile.govex_sub)
        return Response(ConsentModelSerializer.read(consent).data)
