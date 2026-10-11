from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import UserConsent, get_or_create_profile
from .roles import role_of

User = get_user_model()


class ConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserConsent
        fields = ["privacy", "terms", "disclaimer"]


class UserSerializer(serializers.ModelSerializer):
    consent = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    birthdate = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "display_name",
            "birthdate",
            "avatar",
            "role",
            "consent",
        ]

    def get_consent(self, obj):
        consent, _ = UserConsent.objects.get_or_create(user=obj)
        return ConsentSerializer(consent).data

    def get_display_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_avatar(self, obj):
        return get_or_create_profile(obj).avatar

    def get_birthdate(self, obj):
        return get_or_create_profile(obj).birthdate

    def get_role(self, obj):
        return role_of(obj)
