from django.contrib.auth import get_user_model
from rest_framework import serializers

from commons.fields import StrictCharField
from commons.serializers import BaseModelSerializer
from swissfy.social.pictures import PictureField

from .fields import ConsentField, DisplayNameField, RoleField
from .models import UserConsent

User = get_user_model()


class ConsentModelSerializer(BaseModelSerializer):
    class read(BaseModelSerializer.read):
        class Meta(BaseModelSerializer.read.Meta):
            model = UserConsent
            fields = UserConsent.FIELDS


class UserModelSerializer(BaseModelSerializer):
    class read(BaseModelSerializer.read):
        consent = ConsentField()
        display_name = DisplayNameField()
        avatar = serializers.CharField(source="profile.avatar", read_only=True)
        birthdate = serializers.DateField(source="profile.birthdate", read_only=True)
        picture = PictureField()
        role = RoleField(read_only=True)

        class Meta(BaseModelSerializer.read.Meta):
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
                "picture",
                "role",
                "consent",
            ]


class DeviceTokenSerializer(serializers.Serializer):
    token = StrictCharField(required=False, allow_blank=True)
