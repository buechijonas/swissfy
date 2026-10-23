import hmac

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from posts.views import serve_image

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
    has_picture = serializers.SerializerMethodField()

    def get_has_picture(self, profile):
        return bool(profile.public_picture)


class InternalProfileView(APIView):
    authentication_classes = []
    permission_classes = [HasMonolithToken]

    def get(self, request, govex_sub):
        return Response(InternalProfileSerializer(active_profile(govex_sub)).data)


class InternalPictureView(APIView):
    authentication_classes = []
    permission_classes = [HasMonolithToken]

    def get(self, request, govex_sub):
        profile = active_profile(govex_sub)
        if not profile.public_picture:
            return Response(status=404)
        return serve_image(profile.public_picture)


def active_profile(govex_sub):
    return get_object_or_404(
        UserProfile.objects.select_related("user"), govex_sub=govex_sub, user__is_active=True
    )
