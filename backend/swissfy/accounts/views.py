from django.contrib.auth import login, logout
from django.http import Http404
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from commons.views import BaseViewSet

from .consent import push_to_govex
from .devices import find_device, forget_device, keep_or_issue, remember_device
from .models import UserConsent, user_consent
from .serializers import ConsentModelSerializer, DeviceTokenSerializer, UserModelSerializer


class AuthViewSet(BaseViewSet):
    permission_action_classes = {"me": [AllowAny], "restore_device": [AllowAny]}

    def user_data(self, user):
        return UserModelSerializer.read(user, context=self.get_serializer_context()).data

    def device_token(self):
        serializer = DeviceTokenSerializer(data=self.request.data)
        return serializer.validated_data.get("token") if serializer.is_valid() else None

    def me(self, request):
        get_token(request)
        if request.user.is_anonymous:
            return Response({"user": None})
        return Response({"user": self.user_data(request.user)})

    def logout(self, request):
        forget_device(request)
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def sync_device(self, request):
        return Response({"token": keep_or_issue(request, self.device_token())})

    def forget_device(self, request):
        forget_device(request)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def restore_device(self, request):
        device = find_device(self.device_token())
        if device is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        login(request, device.user)
        remember_device(request, device)
        get_token(request)
        return Response({"user": self.user_data(device.user)})

    def accept_consent(self, request, field):
        if field not in UserConsent.FIELDS:
            raise Http404
        consent = user_consent(request.user)
        consent.accept(field)
        push_to_govex(request.user.profile.govex_sub)
        return Response(ConsentModelSerializer.read(consent).data)
