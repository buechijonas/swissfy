import hmac

from django.conf import settings
from rest_framework import serializers, status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from commons.views import BaseViewSet
from swissfy.posts.views.media import serve_image

from .models import UserProfile


class HasMonolithToken(BasePermission):
    def has_permission(self, request, view):
        token = settings.MONOLITH_API_TOKEN
        header = request.headers.get("Authorization", "")
        return bool(token) and hmac.compare_digest(header, f"Bearer {token}")


class InternalProfileSerializer(serializers.Serializer):
    username = serializers.CharField(source="user.username")
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    avatar = serializers.CharField()
    has_picture = serializers.BooleanField(source="has_public_picture")


class InternalProfileViewSet(BaseViewSet):
    authentication_classes = []
    permission_classes = [HasMonolithToken]
    lookup_field = "govex_sub"

    def get_queryset(self):
        return UserProfile.objects.select_related("user").filter(user__is_active=True)

    def retrieve(self, request, govex_sub):
        return Response(InternalProfileSerializer(self.get_object()).data)

    def picture(self, request, govex_sub):
        profile = self.get_object()
        if not profile.public_picture:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return serve_image(profile.public_picture)
