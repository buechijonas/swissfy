from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .consent import CONSENT_FIELDS, push_to_govex
from .devices import find_device, forget_device, keep_or_issue, remember_device
from .models import UserConsent, get_or_create_profile
from .serializers import ConsentSerializer, UserSerializer


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        forget_device(request)
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DeviceTokenView(APIView):
    def post(self, request):
        return Response({"token": keep_or_issue(request, request.data.get("token"))})

    def delete(self, request):
        forget_device(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DeviceRestoreView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        device = find_device(request.data.get("token"))
        if device is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        login(request, device.user)
        remember_device(request, device)
        get_token(request)
        return Response({"user": UserSerializer(device.user, context={"request": request}).data})


class ConsentAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, field):
        if field not in CONSENT_FIELDS:
            return Response(status=status.HTTP_404_NOT_FOUND)
        consent, _ = UserConsent.objects.get_or_create(user=request.user)
        setattr(consent, field, True)
        consent.save(update_fields=[field])
        push_to_govex(get_or_create_profile(request.user).govex_sub)
        return Response(ConsentSerializer(consent).data)


class MeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        get_token(request)
        if request.user.is_authenticated:
            return Response(
                {"user": UserSerializer(request.user, context={"request": request}).data}
            )
        return Response({"user": None})
