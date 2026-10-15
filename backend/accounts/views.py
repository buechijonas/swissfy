from django.contrib.auth import logout
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserConsent
from .serializers import ConsentSerializer, UserSerializer

CONSENT_FIELDS = ["privacy", "terms", "disclaimer"]


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConsentAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, field):
        if field not in CONSENT_FIELDS:
            return Response(status=status.HTTP_404_NOT_FOUND)
        consent, _ = UserConsent.objects.get_or_create(user=request.user)
        setattr(consent, field, True)
        consent.save(update_fields=[field])
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
