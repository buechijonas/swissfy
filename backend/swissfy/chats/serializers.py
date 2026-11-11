import base64
import binascii

from rest_framework import serializers

from commons.fields import StrictCharField
from commons.serializers import BaseModelSerializer
from swissfy.accounts.models import UserProfile

from .models import ChatKey, Message

Protection = UserProfile.ChatProtection

BASE64 = r"^[A-Za-z0-9+/]*={0,2}$"


def base64_field(max_length, **kwargs):
    return serializers.RegexField(BASE64, max_length=max_length, **kwargs)


class EcdhKeySerializer(serializers.Serializer):
    kty = serializers.ChoiceField(["EC"])
    crv = serializers.ChoiceField(["P-256"])
    x = StrictCharField(max_length=100)
    y = StrictCharField(max_length=100)


class PublicKeySerializer(serializers.Serializer):
    ecdh = EcdhKeySerializer()
    kem = base64_field(2000)


class ChatKeyModelSerializer(BaseModelSerializer):
    class read(BaseModelSerializer.read):
        class Meta(BaseModelSerializer.read.Meta):
            model = ChatKey
            fields = ["id", "kind", "public_key"]

    class pin(read):
        class Meta(BaseModelSerializer.read.Meta):
            model = ChatKey
            fields = ["id", "kind", "public_key", "wrapped_private_key", "salt", "iv"]


class ProtectionSerializer(serializers.Serializer):
    mode = serializers.CharField(read_only=True)
    keys = ChatKeyModelSerializer.read(many=True, read_only=True)
    pin_key = ChatKeyModelSerializer.pin(read_only=True, allow_null=True)


class NewKeySerializer(serializers.Serializer):
    public_key = PublicKeySerializer()
    wrapped_private_key = base64_field(10000, required=False)
    salt = base64_field(64, required=False)
    iv = base64_field(32, required=False)


class DeviceKeyInputSerializer(serializers.Serializer):
    public_key = PublicKeySerializer()


class ProtectionInputSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(Protection.choices)
    key = NewKeySerializer(required=False)

    def validate(self, data):
        key = data.get("key")
        if data["mode"] == Protection.STANDARD:
            if key:
                raise serializers.ValidationError("Standard braucht keinen Schlüssel.")
        elif not key:
            raise serializers.ValidationError("Schlüssel fehlt.")
        elif data["mode"] == Protection.PIN and not all(
            key.get(field) for field in ["wrapped_private_key", "salt", "iv"]
        ):
            raise serializers.ValidationError("Der PIN-Schlüssel ist unvollständig.")
        return data


class EnvelopeInputSerializer(serializers.Serializer):
    key = serializers.IntegerField()
    kem = base64_field(2000)
    ecdh = EcdhKeySerializer()
    wrapped = base64_field(100)
    iv = base64_field(32)


class MessageInputSerializer(serializers.Serializer):
    ciphertext = base64_field(20000)
    iv = base64_field(32)
    envelopes = EnvelopeInputSerializer(many=True)
    message_key = base64_field(64, required=False)

    def validate_message_key(self, value):
        try:
            key = base64.b64decode(value, validate=True)
        except binascii.Error:
            key = b""
        if len(key) != 32:
            raise serializers.ValidationError("Ungültiger Schlüssel.")
        return key


class MessageQuerySerializer(serializers.Serializer):
    after = serializers.IntegerField(required=False)
    read = serializers.BooleanField(default=False)


class MessageModelSerializer(BaseModelSerializer):
    class read(BaseModelSerializer.read):
        sender = serializers.CharField(source="sender.username", read_only=True)
        envelopes = serializers.JSONField(source="envelope_data", read_only=True)
        message_key = serializers.CharField(read_only=True, allow_null=True)
        status = serializers.SerializerMethodField()

        class Meta(BaseModelSerializer.read.Meta):
            model = Message
            fields = [
                "id",
                "sender",
                "created_at",
                "ciphertext",
                "iv",
                "envelopes",
                "message_key",
                "status",
            ]

        def get_status(self, obj):
            if obj.sender_id != self.context["viewer"].pk:
                return None
            return obj.status_for(self.context["show_read"])
